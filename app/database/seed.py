from datetime import datetime
from app.database.connection import get_db


# Two fake real-estate companies with different focus areas.
# Each has a custom prompt so the AI agent sounds specific to that company.
COMPANIES = [
    {
        "name": "Sunset Realty",
        "prompt_instructions": (
            "You work for Sunset Realty, a premium home-buying agency. "
            "Your job is to find out if the lead is looking to purchase a home, "
            "what their budget is, and which neighborhoods they prefer. "
            "Be friendly, professional, and concise."
        ),
        "created_at": datetime.utcnow(),
    },
    {
        "name": "CityNest Rentals",
        "prompt_instructions": (
            "You work for CityNest Rentals, which specializes in apartment rentals. "
            "Your goal is to learn if the lead needs a place to rent, "
            "the number of bedrooms they need, and their monthly budget. "
            "Keep the conversation short and natural."
        ),
        "created_at": datetime.utcnow(),
    },
]

# Leads are linked to companies by company_id (inserted after companies are created)
# IMPORTANT: Replace these with real phone numbers before testing outbound calls.
# Free Vapi numbers only support US (+1) numbers.
# Format must be E.164 — e.g. +14085551234 for US, +919876543210 for India (needs paid Vapi plan).
LEADS_TEMPLATE = [
    # Sunset Realty leads
    {"name": "Alice Johnson", "phone": "+14085550101", "status": "PENDING"},
    {"name": "Bob Martinez",  "phone": "+14085550102", "status": "PENDING"},
    {"name": "Carol Smith",   "phone": "+14085550103", "status": "PENDING"},
    # CityNest Rentals leads
    {"name": "David Lee",     "phone": "+14085550201", "status": "PENDING"},
    {"name": "Eva Chen",      "phone": "+14085550202", "status": "PENDING"},
    {"name": "Frank Patel",   "phone": "+14085550203", "status": "PENDING"},
]


async def run_seed():
    db = get_db()

    # Skip if data already exists so re-starting the server doesn't duplicate records
    if await db.companies.count_documents({}) > 0:
        print("Seed data already present, skipping.")
        return

    # Insert companies and grab their generated _ids
    result = await db.companies.insert_many(COMPANIES)
    company_ids = result.inserted_ids
    print(f"Seeded {len(company_ids)} companies")

    # Attach the first 3 leads to Sunset Realty, next 3 to CityNest Rentals
    leads = []
    for i, lead in enumerate(LEADS_TEMPLATE):
        company_index = 0 if i < 3 else 1
        leads.append({
            **lead,
            "company_id": str(company_ids[company_index]),
            "vapi_call_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })

    await db.leads.insert_many(leads)
    print(f"Seeded {len(leads)} leads")
