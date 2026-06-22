import json
from datetime import datetime
from bson import ObjectId
from openai import AsyncOpenAI
import google.generativeai as genai

from app.database.connection import get_db
from app.services.vapi_service import initiate_outbound_call
from app.agent.state import CampaignState, EvaluationState
from app.config import settings

# Primary evaluator — OpenAI GPT-4o-mini (fast, cheap, good at JSON output)
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Fallback evaluator — Google Gemini (used if OpenAI call fails)
genai.configure(api_key=settings.GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")


# ─────────────────────────────────────────────
# Campaign Dispatch Nodes
# ─────────────────────────────────────────────

async def load_company_and_leads(state: CampaignState) -> CampaignState:
    """
    Fetch the company details and all its PENDING leads from the database.
    We need both so we can personalize the Vapi call prompt.
    """
    db = get_db()

    company = await db.companies.find_one({"_id": ObjectId(state["company_id"])})
    if not company:
        raise ValueError(f"Company {state['company_id']} not found")

    company["_id"] = str(company["_id"])

    pending_leads = await db.leads.find({
        "company_id": state["company_id"],
        "status": "PENDING",
    }).to_list(length=100)

    for lead in pending_leads:
        lead["_id"] = str(lead["_id"])

    return {**state, "company": company, "pending_leads": pending_leads}


async def dispatch_calls(state: CampaignState) -> CampaignState:
    """
    For each pending lead, fire an outbound call through Vapi.
    We mark each one CALL_INITIATED right away and store the Vapi call ID
    so we can match the webhook back to the correct lead later.
    """
    db = get_db()
    initiated = []
    errors = []

    for lead in state["pending_leads"]:
        try:
            vapi_response = await initiate_outbound_call(lead, state["company"])
            vapi_call_id = vapi_response.get("id")

            # Update the lead status and store the call ID
            await db.leads.update_one(
                {"_id": ObjectId(lead["_id"])},
                {"$set": {
                    "status": "CALL_INITIATED",
                    "vapi_call_id": vapi_call_id,
                    "updated_at": datetime.utcnow(),
                }},
            )

            # Create a call log entry so we have a record of every call attempt
            await db.call_logs.insert_one({
                "lead_id": lead["_id"],
                "company_id": state["company_id"],
                "vapi_call_id": vapi_call_id,
                "transcript": None,
                "summary": None,
                "llm_reasoning": None,
                "outcome": None,
                "created_at": datetime.utcnow(),
            })

            initiated.append({"lead_id": lead["_id"], "vapi_call_id": vapi_call_id})

        except Exception as e:
            # Don't let one failed call stop the rest — just record it
            errors.append({"lead_id": lead["_id"], "error": str(e)})
            await db.leads.update_one(
                {"_id": ObjectId(lead["_id"])},
                {"$set": {"status": "FAILED", "updated_at": datetime.utcnow()}},
            )

    return {**state, "initiated": initiated, "errors": errors}


# ─────────────────────────────────────────────
# Call Evaluation Nodes (webhook-triggered)
# ─────────────────────────────────────────────

async def load_lead_by_call(state: EvaluationState) -> EvaluationState:
    """
    Find the lead that corresponds to this Vapi call ID.
    Also load the company so we have context for the LLM prompt.
    """
    db = get_db()

    lead = await db.leads.find_one({"vapi_call_id": state["vapi_call_id"]})
    if not lead:
        raise ValueError(f"No lead found for call ID {state['vapi_call_id']}")

    lead["_id"] = str(lead["_id"])

    company = await db.companies.find_one({"_id": ObjectId(lead["company_id"])})
    company["_id"] = str(company["_id"])

    return {**state, "lead": lead, "company": company}


async def evaluate_transcript(state: EvaluationState) -> EvaluationState:
    """
    Classify the lead outcome using the call transcript.
    OpenAI (GPT-4o-mini) is the primary evaluator.
    If that fails for any reason, we fall back to Google Gemini.
    Either way, if we can't be confident, we return NEEDS_REVIEW
    so a human can follow up instead of auto-categorizing wrongly.
    """
    transcript = state.get("transcript") or state.get("summary") or ""

    if not transcript.strip():
        return {**state, "verdict": "FAILED", "reasoning": "Transcript was empty"}

    prompt = _build_eval_prompt(transcript, state["company"])

    # Try OpenAI first
    try:
        raw = await _call_openai(prompt)
    except Exception as openai_err:
        # OpenAI failed — try Google Gemini before giving up
        print(f"OpenAI evaluation failed ({openai_err}), falling back to Gemini")
        try:
            raw = await _call_gemini(prompt)
        except Exception as gemini_err:
            print(f"Gemini fallback also failed: {gemini_err}")
            return {**state, "verdict": "NEEDS_REVIEW", "reasoning": "Both LLMs failed — flagged for manual review"}

    try:
        result = json.loads(raw)
        verdict = result.get("verdict", "NEEDS_REVIEW")
        reasoning = result.get("reasoning", "")
    except json.JSONDecodeError:
        verdict = "NEEDS_REVIEW"
        reasoning = f"Could not parse LLM response: {raw}"

    # Guard against the model hallucinating a different status value
    if verdict not in ("QUALIFIED", "NOT_INTERESTED", "NEEDS_REVIEW"):
        verdict = "NEEDS_REVIEW"

    return {**state, "verdict": verdict, "reasoning": reasoning}


def _build_eval_prompt(transcript: str, company: dict) -> str:
    return f"""You are analyzing a completed real estate sales call transcript.

Company: {company['name']}
Company Focus: {company['prompt_instructions']}

Call Transcript:
{transcript}

Classify the lead into exactly one of these categories:
- QUALIFIED: The customer expressed clear interest (wants to buy/sell/rent, asked questions, gave details)
- NOT_INTERESTED: The customer clearly declined or said they are not interested
- NEEDS_REVIEW: The call was too short, confusing, inconclusive, or you are not confident

Return ONLY valid JSON, nothing else:
{{
    "verdict": "QUALIFIED" | "NOT_INTERESTED" | "NEEDS_REVIEW",
    "reasoning": "one sentence explanation"
}}"""


async def _call_openai(prompt: str) -> str:
    response = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=256,
        response_format={"type": "json_object"},  # forces valid JSON output
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


async def _call_gemini(prompt: str) -> str:
    # Gemini's Python SDK is synchronous, so we call it directly
    # (acceptable here since it's only a fallback path)
    response = gemini_model.generate_content(prompt)
    return response.text.strip()


async def persist_outcome(state: EvaluationState) -> EvaluationState:
    """
    Write the final verdict back to MongoDB — update the lead status
    and fill in the call log with the transcript and LLM reasoning.
    """
    db = get_db()
    lead_id = state["lead"]["_id"]

    await db.leads.update_one(
        {"_id": ObjectId(lead_id)},
        {"$set": {
            "status": state["verdict"],
            "updated_at": datetime.utcnow(),
        }},
    )

    await db.call_logs.update_one(
        {"vapi_call_id": state["vapi_call_id"]},
        {"$set": {
            "transcript": state.get("transcript"),
            "summary": state.get("summary"),
            "llm_reasoning": state.get("reasoning"),
            "outcome": state["verdict"],
        }},
    )

    return state
