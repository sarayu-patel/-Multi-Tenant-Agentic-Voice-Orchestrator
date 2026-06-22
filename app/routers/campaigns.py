from fastapi import APIRouter, HTTPException

from app.agent.graph import campaign_graph

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.post("/{company_id}/trigger")
async def trigger_campaign(company_id: str):
    """
    Kicks off outbound calls for every PENDING lead belonging to this company.
    The LangGraph campaign_graph handles the full flow:
      1. Load the company + pending leads
      2. Call Vapi for each lead
      3. Mark them as CALL_INITIATED in MongoDB

    Returns a summary of what was initiated and what (if anything) failed.
    """
    try:
        initial_state = {
            "company_id": company_id,
            "company": {},
            "pending_leads": [],
            "initiated": [],
            "errors": [],
        }
        result = await campaign_graph.ainvoke(initial_state)

        return {
            "company_id": company_id,
            "calls_initiated": len(result["initiated"]),
            "calls_failed": len(result["errors"]),
            "details": result["initiated"],
            "errors": result["errors"],
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Campaign failed: {str(e)}")
