from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from datetime import datetime

from app.database.connection import get_db
from app.database.models import LeadCreate, LeadStatusUpdate

router = APIRouter(prefix="/api/leads", tags=["leads"])


def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


@router.get("/")
async def list_leads(company_id: str = Query(None)):
    """
    Return all leads. Pass ?company_id=... to filter by tenant.
    The frontend uses this to populate the lead directory.
    """
    db = get_db()
    query = {}
    if company_id:
        query["company_id"] = company_id

    leads = await db.leads.find(query).to_list(length=500)
    return [_serialize(l) for l in leads]


@router.get("/{lead_id}")
async def get_lead(lead_id: str):
    db = get_db()
    lead = await db.leads.find_one({"_id": ObjectId(lead_id)})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return _serialize(lead)


@router.post("/", status_code=201)
async def create_lead(body: LeadCreate):
    db = get_db()
    # Make sure the company exists before creating the lead
    company = await db.companies.find_one({"_id": ObjectId(body.company_id)})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    doc = {
        **body.model_dump(),
        "status": "PENDING",
        "vapi_call_id": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = await db.leads.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize(doc)


@router.patch("/{lead_id}/status")
async def update_lead_status(lead_id: str, body: LeadStatusUpdate):
    """Manual status override — useful for testing without a real Vapi call."""
    db = get_db()
    result = await db.leads.update_one(
        {"_id": ObjectId(lead_id)},
        {"$set": {"status": body.status, "updated_at": datetime.utcnow()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Status updated", "status": body.status}
