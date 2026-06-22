import httpx
from app.config import settings

VAPI_BASE_URL = "https://api.vapi.ai"


def _headers():
    return {"Authorization": f"Bearer {settings.VAPI_API_KEY}"}


async def initiate_outbound_call(lead: dict, company: dict) -> dict:
    """
    Kick off a call to the lead via Vapi.
    We build the assistant inline so the system prompt is specific to the company —
    this avoids needing a pre-created assistant for every tenant.
    """
    system_prompt = _build_system_prompt(lead, company)

    payload = {
        "phoneNumberId": settings.VAPI_PHONE_NUMBER_ID,
        "customer": {
            "name": lead["name"],
            "number": lead["phone"],
        },
        "assistant": {
            "firstMessage": (
                f"Hi {lead['name']}, this is an assistant calling from {company['name']}. "
                "Do you have a quick moment to chat?"
            ),
            "transcriber": {
                "provider": "deepgram",
                "model": "nova-2",
                "language": "en",
            },
            "model": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "messages": [{"role": "system", "content": system_prompt}],
            },
            "voice": {
                "provider": "11labs",
                "voiceId": "21m00Tcm4TlvDq8ikWAM",  # "Rachel" — available on all 11labs accounts
            },
        },
    }
    # Note: serverUrl is intentionally omitted — Vapi falls back to the
    # account-level server URL configured in the dashboard

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{VAPI_BASE_URL}/call/phone",
            headers=_headers(),
            json=payload,
            timeout=30,
        )
        if response.status_code >= 400:
            # Print the full Vapi error so we can debug payload issues
            print(f"Vapi error {response.status_code}: {response.text}")
        response.raise_for_status()
        return response.json()


def _build_system_prompt(lead: dict, company: dict) -> str:
    """
    Combines the company's custom instructions with lead-specific context.
    This is the 'dynamic prompting' bonus requirement.
    """
    return (
        f"{company['prompt_instructions']}\n\n"
        f"You are currently speaking with {lead['name']}. "
        "Keep the call under 3 minutes. "
        "At the end, summarize what the customer said about their intent."
    )


async def get_call_details(vapi_call_id: str) -> dict:
    """Fetch full call details from Vapi (useful for debugging)."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{VAPI_BASE_URL}/call/{vapi_call_id}",
            headers=_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
