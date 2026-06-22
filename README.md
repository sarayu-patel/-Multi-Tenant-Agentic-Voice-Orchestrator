# Voice Agent — Multi-Tenant Outbound Calling System

FastAPI + LangGraph + Vapi AI + MongoDB

## Quick Start

```bash
cd voice-agent
cp .env.example .env        # fill in your keys
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs to see the interactive API docs.

---

## Environment Variables

| Key | Where to get it |
|-----|----------------|
| `MONGODB_URI` | MongoDB Atlas → Connect → Drivers |
| `VAPI_API_KEY` | app.vapi.ai → Account → API Keys |
| `VAPI_PHONE_NUMBER_ID` | app.vapi.ai → Phone Numbers |
| `ANTHROPIC_API_KEY` | console.anthropic.com |

---

## API Endpoints

| Method | Path | What it does |
|--------|------|--------------|
| GET | `/api/companies` | List all tenants |
| GET | `/api/leads?company_id=...` | List leads (filter by tenant) |
| POST | `/api/campaigns/{company_id}/trigger` | Start outbound calls for all PENDING leads |
| POST | `/api/webhooks/vapi` | Vapi fires this when a call ends |
| PATCH | `/api/leads/{id}/status` | Manually override a lead's status (testing) |

---

## LangGraph Architecture

**Campaign Graph** — triggered by `POST /api/campaigns/{id}/trigger`

```
load_company_and_leads → dispatch_calls → END
```

- `load_company_and_leads`: fetches company details + PENDING leads from MongoDB
- `dispatch_calls`: calls Vapi REST API for each lead, marks them CALL_INITIATED

**Evaluation Graph** — triggered by `POST /api/webhooks/vapi`

```
load_lead_by_call → evaluate_transcript → persist_outcome → END
```

- `load_lead_by_call`: finds the lead using the Vapi call ID
- `evaluate_transcript`: sends transcript to Claude, returns QUALIFIED / NOT_INTERESTED / NEEDS_REVIEW
- `persist_outcome`: writes the verdict back to MongoDB

The `NEEDS_REVIEW` status is the human-in-the-loop flag — Claude sets this when the transcript is too short, ambiguous, or contradictory.

---

## Vapi Webhook Setup

1. In your Vapi dashboard, go to **Account → Server URL**
2. Set it to `https://your-cloud-run-url/api/webhooks/vapi`
3. Vapi will POST `end-of-call-report` events there automatically

---

## Deploy to GCP Cloud Run

```bash
chmod +x deploy.sh
# Edit PROJECT_ID inside deploy.sh first
./deploy.sh
```

---

## Seeded Data

On first startup the app creates:
- **Sunset Realty** (house buying) with 3 leads: Alice, Bob, Carol
- **CityNest Rentals** (apartment rentals) with 3 leads: David, Eva, Frank

All leads start as `PENDING`.
