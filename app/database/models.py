from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class LeadStatus(str, Enum):
    PENDING = "PENDING"
    CALL_INITIATED = "CALL_INITIATED"
    QUALIFIED = "QUALIFIED"
    NOT_INTERESTED = "NOT_INTERESTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"   # LLM wasn't confident — human should check
    FAILED = "FAILED"               # Vapi call itself failed (bad number, no answer, etc.)


# --- Request/Response bodies used by routers ---

class CompanyCreate(BaseModel):
    name: str
    prompt_instructions: str  # e.g. "You work for Sunset Realty, a house-buying company..."


class LeadCreate(BaseModel):
    company_id: str
    name: str
    phone: str  # E.164 format, e.g. +14155552671


class LeadStatusUpdate(BaseModel):
    status: LeadStatus
