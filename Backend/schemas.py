from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid


# ── Prospect Schemas ───────────────────────────────────────────────────────────

class ProspectBase(BaseModel):
    """Fields shared between creating and reading a prospect."""
    email: str
    name: Optional[str] = None
    first_name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    linkedin_url: Optional[str] = None


class ProspectCreate(ProspectBase):
    """What we need to manually create a prospect (POST /api/leads)."""
    pass  # same as base for now


class ProspectResponse(ProspectBase):
    """What we return when someone asks for a prospect (GET /api/leads)."""
    id: uuid.UUID
    icp_score: Optional[float] = None
    urgency_score: Optional[float] = None
    signal_flags: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True  # allows converting SQLAlchemy model → Pydantic model


# ── Lead Discovery Schemas ─────────────────────────────────────────────────────

class LeadDiscoverRequest(BaseModel):
    """
    What the frontend sends when asking us to find leads.
    The user types a description of their ideal customer.
    """
    icp_description: str          # "VP of Sales at B2B SaaS, 50-500 employees, US"
    max_leads: Optional[int] = 10  # how many leads to fetch

    # Optional Apollo filters — if not provided, we infer from icp_description
    titles: Optional[List[str]] = None        # ["VP of Sales", "Head of Sales"]
    industries: Optional[List[str]] = None    # ["Software", "SaaS"]
    employee_ranges: Optional[List[str]] = None  # ["51,200", "201,500"]
    locations: Optional[List[str]] = None     # ["United States"]


class LeadDiscoverResponse(BaseModel):
    """What we return after discovering leads."""
    total_found: int
    leads_stored: int
    leads: List[ProspectResponse]
    message: str


# ── Campaign Schemas ───────────────────────────────────────────────────────────

class CampaignStep(BaseModel):
    """One step in a campaign sequence."""
    step: int
    channel: str = "email"
    delay_days: int
    goal: str   # awareness | value_add | meeting_ask | breakup


class CampaignCreate(BaseModel):
    """What we need to create a campaign."""
    name: str
    icp_description: str
    value_prop: str
    tone: Optional[str] = "concise"
    banned_phrases: Optional[List[str]] = []
    steps: Optional[List[CampaignStep]] = [
        CampaignStep(step=1, delay_days=0,  goal="awareness"),
        CampaignStep(step=2, delay_days=3,  goal="value_add"),
        CampaignStep(step=3, delay_days=7,  goal="meeting_ask"),
        CampaignStep(step=4, delay_days=12, goal="breakup"),
    ]


class CampaignResponse(CampaignCreate):
    """What we return when reading a campaign."""
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True