from fastapi import APIRouter, Request, HTTPException
from app.agent.graph import evaluation_graph

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/vapi")
async def handle_vapi_webhook(request: Request):
    """
    Vapi POSTs here when a call finishes (end-of-call-report event).
    We extract the call ID and transcript, then run the evaluation graph
    to classify the lead and update the database.

    Vapi's webhook payload can come in two shapes depending on SDK version,
    so we handle both — the body might wrap everything under a 'message' key
    or the fields might be at the top level.
    """
    # Read raw bytes first so we can log it if something goes wrong
    raw = await request.body()

    if not raw:
        # Vapi sometimes sends empty pings to verify the endpoint is alive
        print("Vapi webhook: received empty body (likely a connectivity check)")
        return {"status": "ok"}

    try:
        import json
        body = json.loads(raw)
    except json.JSONDecodeError:
        print(f"Vapi webhook: non-JSON body received: {raw[:500]}")
        return {"status": "ignored", "reason": "non-json body"}

    # Log every incoming event during development so we can inspect the shape
    event_type = body.get("message", {}).get("type") or body.get("type", "unknown")
    print(f"Vapi webhook event: {event_type}")
    print(f"Vapi webhook payload: {json.dumps(body, indent=2)[:1000]}")

    # Normalize — Vapi wraps newer events under a 'message' key
    message = body.get("message", body)
    event_type = message.get("type", "")

    # Only process the final call report; everything else is informational
    if event_type != "end-of-call-report":
        return {"status": "ignored", "type": event_type}

    call = message.get("call", {})
    vapi_call_id = call.get("id")
    transcript = message.get("transcript", "")
    summary = message.get("summary", "")

    if not vapi_call_id:
        raise HTTPException(status_code=400, detail="Missing call.id in webhook payload")

    try:
        initial_state = {
            "vapi_call_id": vapi_call_id,
            "transcript": transcript,
            "summary": summary,
            "lead": None,
            "company": None,
            "verdict": None,
            "reasoning": None,
        }
        result = await evaluation_graph.ainvoke(initial_state)

        return {
            "status": "processed",
            "vapi_call_id": vapi_call_id,
            "verdict": result["verdict"],
            "reasoning": result["reasoning"],
        }

    except ValueError as e:
        # Lead not found — could be a test call from the Vapi dashboard
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
