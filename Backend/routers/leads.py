# backend/routers/leads.py
# All API endpoints related to leads/prospects
# This file handles: finding leads, storing them, retrieving them

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from database import get_db
from models import Prospect
from schemas import (
    ProspectCreate,
    ProspectResponse,
    LeadDiscoverRequest,
    LeadDiscoverResponse
)
from services.apollo import search_people
from services.scoring import score_batch

# APIRouter works exactly like FastAPI app but scoped to /api/leads
# prefix="/api/leads" means every route here starts with /api/leads
router = APIRouter(prefix="/api/leads", tags=["Leads"])


# ── GET /api/leads ─────────────────────────────────────────────────────────────
@router.get("/", response_model=List[ProspectResponse])
def get_leads(
    skip: int = Query(0, description="How many records to skip (for pagination)"),
    limit: int = Query(50, description="Max records to return"),
    min_icp_score: Optional[float] = Query(None, description="Filter by minimum ICP score"),
    db: Session = Depends(get_db)
):
    """
    Get all stored leads with optional filtering.

    Pagination example:
    - Page 1: skip=0,  limit=50
    - Page 2: skip=50, limit=50
    - Page 3: skip=100, limit=50
    """
    query = db.query(Prospect)

    # Apply ICP score filter if provided
    if min_icp_score is not None:
        query = query.filter(Prospect.icp_score >= min_icp_score)

    # Order by best ICP match first
    query = query.order_by(Prospect.icp_score.desc())

    leads = query.offset(skip).limit(limit).all()
    return leads


# ── GET /api/leads/{id} ────────────────────────────────────────────────────────
@router.get("/{lead_id}", response_model=ProspectResponse)
def get_lead(lead_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a single lead by ID."""
    lead = db.query(Prospect).filter(Prospect.id == lead_id).first()
    if not lead:
        # HTTPException automatically returns proper JSON error response
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


# ── POST /api/leads ────────────────────────────────────────────────────────────
@router.post("/", response_model=ProspectResponse)
def create_lead(lead_data: ProspectCreate, db: Session = Depends(get_db)):
    """
    Manually create a lead (without Apollo discovery).
    Useful for testing or adding known contacts.
    """
    # Check if lead already exists (email is unique)
    existing = db.query(Prospect).filter(
        Prospect.email == lead_data.email
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,   # 409 Conflict = resource already exists
            detail=f"Lead with email {lead_data.email} already exists"
        )

    # Create SQLAlchemy model from Pydantic input
    # model_dump() converts Pydantic model → plain Python dict
    prospect = Prospect(**lead_data.model_dump())
    db.add(prospect)
    db.commit()
    db.refresh(prospect)   # reload from DB to get generated id, created_at etc.
    return prospect


# ── POST /api/leads/discover ───────────────────────────────────────────────────
@router.post("/discover", response_model=LeadDiscoverResponse)
async def discover_leads(
    request: LeadDiscoverRequest,
    db: Session = Depends(get_db)
):
    """
    THE MAIN ENDPOINT: Given an ICP description, find and score real leads.

    Flow:
    1. Call Apollo API with filters
    2. Score all leads against ICP description (batch cosine similarity)
    3. Store new leads in Postgres (skip duplicates)
    4. Return scored + sorted leads

    Note: Apollo free tier = 50 exports/month. Use wisely!
    """

    # Step 1: Fetch leads from Apollo
    try:
        raw_leads = await search_people(
            titles=request.titles,
            locations=request.locations,
            employee_ranges=request.employee_ranges,
            industries=request.industries,
            max_leads=request.max_leads
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,   # 502 Bad Gateway = upstream API failed
            detail=f"Apollo API error: {str(e)}"
        )

    if not raw_leads:
        return LeadDiscoverResponse(
            total_found=0,
            leads_stored=0,
            leads=[],
            message="No leads found matching your ICP. Try broader filters."
        )

    # Step 2: Score all leads at once (batch is faster than one-by-one)
    icp_scores = score_batch(request.icp_description, raw_leads)

    # Step 3: Store in database (skip duplicates)
    stored_leads = []
    skipped = 0

    for lead_data, icp_score in zip(raw_leads, icp_scores):
        # Check if this email already exists in our DB
        existing = db.query(Prospect).filter(
            Prospect.email == lead_data["email"]
        ).first()

        if existing:
            skipped += 1
            stored_leads.append(existing)
            continue

        # Create new prospect record
        prospect = Prospect(
            email=lead_data["email"],
            name=lead_data.get("name"),
            first_name=lead_data.get("first_name"),
            title=lead_data.get("title"),
            company=lead_data.get("company"),
            linkedin_url=lead_data.get("linkedin_url"),
            icp_score=icp_score,
            enrichment=lead_data.get("enrichment", {}),
            signal_flags=[],      # will be populated by enrichment worker later
            urgency_score=0.0,    # will be calculated after signal detection
        )
        db.add(prospect)
        stored_leads.append(prospect)

    db.commit()

    # Refresh all stored leads to get DB-generated fields
    for lead in stored_leads:
        db.refresh(lead)

    # Sort by ICP score descending before returning
    stored_leads.sort(key=lambda x: x.icp_score or 0, reverse=True)

    return LeadDiscoverResponse(
        total_found=len(raw_leads),
        leads_stored=len(raw_leads) - skipped,
        leads=stored_leads,
        message=f"Found {len(raw_leads)} leads, stored {len(raw_leads) - skipped} new ({skipped} already existed)"
    )


# ── DELETE /api/leads/{id} ─────────────────────────────────────────────────────
@router.delete("/{lead_id}")
def delete_lead(lead_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a lead. Useful for removing test data."""
    lead = db.query(Prospect).filter(Prospect.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.delete(lead)
    db.commit()
    return {"message": f"Lead {lead_id} deleted"}