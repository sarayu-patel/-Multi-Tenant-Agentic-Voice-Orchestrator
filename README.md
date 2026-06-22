# Voice Agent — Multi-Tenant Agentic Voice Orchestrator

FastAPI + LangGraph + Vapi AI + Google Gemini/OpenAI + MongoDB Atlas

## Live Demo

🚀 Deployment URL

https://multi-tenant-agentic-voice.onrender.com/

## GitHub Repository

📂 Repository

https://github.com/sarayu-patel/-Multi-Tenant-Agentic-Voice-Orchestrator

---

## Project Overview

The Multi-Tenant Agentic Voice Orchestrator is an AI-powered outbound calling platform that automates customer outreach for multiple companies.

The system allows companies to:

* Manage leads
* Launch AI-powered outbound calling campaigns
* Analyze customer conversations using LLMs
* Automatically classify lead outcomes
* Store call history and evaluations in MongoDB Atlas

The application supports multiple tenants (companies), each with its own leads and campaign instructions.

---

## Quick Start

```bash
git clone https://github.com/sarayu-patel/-Multi-Tenant-Agentic-Voice-Orchestrator.git

cd voice-agent

cp .env.example .env

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000
```

API Documentation:

```text
http://localhost:8000/docs
```

---

## Environment Variables

| Key                  | Description                     |
| -------------------- | ------------------------------- |
| MONGODB_URI          | MongoDB Atlas connection string |
| MONGODB_DB_NAME      | Database name (voice_agent)     |
| VAPI_API_KEY         | Vapi API key                    |
| VAPI_PHONE_NUMBER_ID | Outbound Vapi phone number      |
| GOOGLE_API_KEY       | Google Gemini API key           |
| OPENAI_API_KEY       | Optional OpenAI API key         |

---

## API Endpoints

| Method | Path                                | Description                      |
| ------ | ----------------------------------- | -------------------------------- |
| GET    | /api/companies                      | List all companies               |
| GET    | /api/leads?company_id=...           | List leads for a company         |
| POST   | /api/campaigns/{company_id}/trigger | Start outbound calling campaign  |
| POST   | /api/webhooks/vapi                  | Receives Vapi end-of-call events |
| PATCH  | /api/leads/{id}/status              | Update lead status manually      |

---

## System Workflow

### 1. Company Management

Companies are created with:

* Company Name
* Prompt Instructions
* Business Context

### 2. Lead Management

Each company maintains its own:

* Customer Leads
* Phone Numbers
* Lead Status

### 3. Campaign Execution

When a campaign is triggered:

```text
load_company_and_leads
        ↓
dispatch_calls
        ↓
END
```

#### load_company_and_leads

* Loads company details
* Loads all PENDING leads

#### dispatch_calls

* Initiates outbound calls through Vapi
* Updates lead status to CALL_INITIATED
* Creates call log entries

---

## AI Evaluation Workflow

Triggered automatically when Vapi sends an end-of-call webhook.

```text
load_lead_by_call
        ↓
evaluate_transcript
        ↓
persist_outcome
        ↓
END
```

### load_lead_by_call

Finds the lead using:

```text
vapi_call_id
```

### evaluate_transcript

Analyzes conversation transcript using:

* OpenAI GPT-4o-mini (Primary)
* Google Gemini (Fallback)

Returns:

```text
QUALIFIED
NOT_INTERESTED
NEEDS_REVIEW
```

### persist_outcome

Stores:

* Transcript
* Summary
* AI reasoning
* Final outcome

in MongoDB Atlas.

---

## Lead Classification

### QUALIFIED

Customer shows clear buying/renting interest.

### NOT_INTERESTED

Customer explicitly declines.

### NEEDS_REVIEW

Conversation is:

* Too short
* Ambiguous
* Inconclusive

This acts as the Human-in-the-Loop review mechanism.

---

## Database Collections

### companies

Stores company information.

### leads

Stores:

* Customer details
* Phone numbers
* Lead status

### call_logs

Stores:

* Vapi Call ID
* Transcript
* Summary
* LLM Reasoning
* Final Outcome
* Timestamps

---

## Tech Stack

### Backend

* FastAPI
* Python 3.12

### AI & Orchestration

* LangGraph
* OpenAI GPT-4o-mini
* Google Gemini

### Voice Platform

* Vapi AI

### Database

* MongoDB Atlas
* Motor

### Frontend

* HTML
* CSS
* JavaScript

### Deployment

* Docker
* Render

---

## Vapi Webhook Setup

In Vapi Dashboard:

```text
Account
   ↓
Server URL
```

Configure:

```text
https://multi-tenant-agentic-voice.onrender.com/api/webhooks/vapi
```

Vapi automatically sends:

```text
end-of-call-report
```

events to the application.

---

## Deployment

The application is deployed on Render.

Live URL:

https://multi-tenant-agentic-voice.onrender.com/

MongoDB Atlas is used as the cloud database.

---

## Seeded Data

On first startup the application creates:

### Sunset Realty

House buying campaign

Leads:

* Alice
* Bob
* Carol

### CityNest Rentals

Apartment rental campaign

Leads:

* David
* Eva
* Frank

All leads start with:

```text
PENDING
```

status.

---

## Future Enhancements

* Campaign Scheduling
* Analytics Dashboard
* Multi-language Calling
* CRM Integration
* Real-time Monitoring
* Advanced Lead Scoring

---

## Author

**Sarayu Patel**

B.Tech Computer Science & Engineering (AI & DS)

Parul University
