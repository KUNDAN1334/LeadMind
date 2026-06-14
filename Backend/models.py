# backend/models.py

from sqlalchemy import (
    Column, String, Float, Integer, Boolean,
    Text, ARRAY, TIMESTAMP, ForeignKey, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from database import Base
import uuid


# ── Prospects ──────────────────────────────────────────────────────────────────
# Every person we find as a potential lead lives here
class Prospect(Base):
    __tablename__ = "prospects"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email        = Column(String, unique=True, nullable=False)
    name         = Column(String)
    first_name   = Column(String)
    title        = Column(String)                    # "VP of Sales"
    company      = Column(String)
    linkedin_url = Column(String)
    icp_score    = Column(Float)                     # 0-1: how well they match our ideal customer
    urgency_score= Column(Float)                     # 0-1: how urgent is outreach (based on signals)
    enrichment   = Column(JSONB)                     # raw data from Apollo, LinkedIn, NewsAPI
    signal_flags = Column(ARRAY(Text))               # ['hiring_sdrs', 'fundraising', ...]
    created_at   = Column(TIMESTAMP(timezone=True), server_default=func.now())


# ── Campaigns ──────────────────────────────────────────────────────────────────
# A campaign is a sequence of emails targeting a specific type of prospect
class Campaign(Base):
    __tablename__ = "campaigns"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name            = Column(String, nullable=False)
    icp_description = Column(Text)                   # "VP Sales at B2B SaaS, 50-500 employees"
    value_prop      = Column(Text)                   # what we're selling / offering
    tone            = Column(String, default="concise")  # concise|friendly|direct|formal
    banned_phrases  = Column(ARRAY(Text))            # words to never use
    steps           = Column(JSONB)                  # [{channel, delay_days, goal}, ...]
    created_at      = Column(TIMESTAMP(timezone=True), server_default=func.now())


# ── Enrollments ────────────────────────────────────────────────────────────────
# Links a prospect to a campaign and tracks where they are in the sequence
class Enrollment(Base):
    __tablename__ = "enrollments"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prospect_id    = Column(UUID(as_uuid=True), ForeignKey("prospects.id"))
    campaign_id    = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    # State machine: enrolled → contacted → replied → booked / cold / unsubscribed
    state          = Column(String, default="enrolled")
    current_step   = Column(Integer, default=0)
    variant_bucket = Column(String)                  # 'behavioral' | 'standard' (A/B test)
    enrolled_at    = Column(TIMESTAMP(timezone=True), server_default=func.now())


# ── Emails ─────────────────────────────────────────────────────────────────────
# Every email sent is logged here
class Email(Base):
    __tablename__ = "emails"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("enrollments.id"))
    step_num      = Column(Integer)
    subject       = Column(Text)
    body          = Column(Text)
    hook_type     = Column(String)                   # 'behavioral'|'standard'|'funding'|'hiring'
    hook_source   = Column(Text)                     # the post/signal that generated the hook
    hook_score    = Column(Float)                    # relevance score 0-1
    sent_at       = Column(TIMESTAMP(timezone=True))
    opened_at     = Column(TIMESTAMP(timezone=True))
    replied_at    = Column(TIMESTAMP(timezone=True))


# ── Replies ────────────────────────────────────────────────────────────────────
# Every inbound reply from a prospect
class Reply(Base):
    __tablename__ = "replies"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_id          = Column(UUID(as_uuid=True), ForeignKey("emails.id"))
    prospect_id       = Column(UUID(as_uuid=True), ForeignKey("prospects.id"))
    body              = Column(Text)
    # What does this reply mean? INTERESTED|OBJECTION|QUESTION|UNSUBSCRIBE|OOO|ANGRY
    intent            = Column(String)
    intent_confidence = Column(Float)
    received_at       = Column(TIMESTAMP(timezone=True))
    response_sent     = Column(Boolean, default=False)
    response_body     = Column(Text)
    turn_number       = Column(Integer)              # which turn in the conversation is this?


# ── Conversation States ─────────────────────────────────────────────────────────
# KEY DIFFERENTIATOR: explicit structured memory of every conversation
class ConversationState(Base):
    __tablename__ = "conversation_states"

    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prospect_id          = Column(UUID(as_uuid=True), ForeignKey("prospects.id"))
    campaign_id          = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    # Where is this conversation right now?
    stage                = Column(String, default="exploring")  # exploring|objecting|scheduling|escalated|closed
    open_questions       = Column(ARRAY(Text))       # questions prospect asked, not yet answered
    objections_raised    = Column(ARRAY(Text))       # all objections seen so far
    objections_addressed = Column(ARRAY(Text))       # objections we've already handled (don't repeat!)
    commitments_made     = Column(ARRAY(Text))       # things WE promised to do
    prospect_pain_signal = Column(Text)              # their exact words about their pain
    prior_claims         = Column(JSONB)             # facts we've stated (for consistency checking)
    turn_count           = Column(Integer, default=0)
    escalated            = Column(Boolean, default=False)
    updated_at           = Column(TIMESTAMP(timezone=True), server_default=func.now())


# ── Meeting Outcomes ───────────────────────────────────────────────────────────
# What happened AFTER the meeting? This closes the revenue loop
class MeetingOutcome(Base):
    __tablename__ = "meeting_outcomes"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prospect_id = Column(UUID(as_uuid=True), ForeignKey("prospects.id"))
    meeting_at  = Column(TIMESTAMP(timezone=True))
    # showed_up|no_show|qualified|unqualified|closed|lost
    outcome     = Column(String)
    deal_value  = Column(Numeric)
    loss_reason = Column(String)                     # not_budget|not_timing|competitor|not_interested
    recorded_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


# ── Analytics Events ───────────────────────────────────────────────────────────
# Every important thing that happens is logged as an event
# This is what powers the analytics dashboard
class Event(Base):
    __tablename__ = "events"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type        = Column(String)     # email_sent|opened|replied|meeting_booked|meeting_outcome
    prospect_id = Column(UUID(as_uuid=True), ForeignKey("prospects.id"))
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    metadata    = Column(JSONB)      # flexible: any extra data relevant to this event
    occurred_at = Column(TIMESTAMP(timezone=True), server_default=func.now())