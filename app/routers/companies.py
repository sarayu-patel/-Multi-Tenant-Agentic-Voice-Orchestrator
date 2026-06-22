from fastapi import APIRouter, HTTPException
from bson import ObjectId

from app.database.connection import get_db
from app.database.models import CompanyCreate

router = APIRouter(prefix="/api/companies", tags=["companies"])


def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


@router.get("/")
async def list_companies():
    db = get_db()
    companies = await db.companies.find().to_list(length=100)
    return [_serialize(c) for c in companies]


@router.get("/{company_id}")
async def get_company(company_id: str):
    db = get_db()
    company = await db.companies.find_one({"_id": ObjectId(company_id)})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return _serialize(company)


@router.post("/", status_code=201)
async def create_company(body: CompanyCreate):
    db = get_db()
    from datetime import datetime
    doc = {**body.model_dump(), "created_at": datetime.utcnow()}
    result = await db.companies.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize(doc)
