from typing import TypedDict, Optional


# State for the campaign dispatch flow
# (triggered when admin hits "Trigger Campaign" for a company)
class CampaignState(TypedDict):
    company_id: str
    company: dict                   # company document from MongoDB
    pending_leads: list             # leads with status=PENDING
    initiated: list                 # [{lead_id, vapi_call_id}, ...]
    errors: list                    # any leads we failed to call


# State for the webhook evaluation flow
# (triggered when Vapi sends us an end-of-call webhook)
class EvaluationState(TypedDict):
    vapi_call_id: str
    transcript: str
    summary: str
    lead: Optional[dict]            # lead document from MongoDB
    company: Optional[dict]         # company document from MongoDB
    verdict: Optional[str]          # QUALIFIED | NOT_INTERESTED | NEEDS_REVIEW
    reasoning: Optional[str]        # LLM's explanation for the verdict
