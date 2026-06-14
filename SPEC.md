# LeadMind — Full Project Specification
 
> **Portfolio project targeting Artisan AI's AI Engineer (Remote) role**
> End-to-end autonomous AI sales agent — built entirely on **free/open-source tools**
> Version 1.0 | Author: Kundan Solanki
 
---
 
## Table of Contents
 
1. [Vision & Positioning](#1-vision--positioning)
2. [What Artisan Does vs What LeadMind Does Better](#2-what-artisan-does-vs-what-leadmind-does-better)
3. [System Architecture](#3-system-architecture)
4. [Tech Stack (100% Free)](#4-tech-stack-100-free)
5. [Data Models](#5-data-models)
6. [Feature Specifications](#6-feature-specifications)
   - F1: Lead Discovery & ICP Matching
   - F2: Enrichment Pipeline
   - F3: Behavioral Personalization Engine *(Gap Fix #1)*
   - F4: Email Generation with Variant A/B
   - F5: Campaign Sequence Engine
   - F6: Stateful Multi-Turn Reply Handler *(Gap Fix #2)*
   - F7: Revenue Feedback Loop *(Gap Fix #3 — NEW)*
   - F8: Meeting Booking
   - F9: Analytics Dashboard
7. [AI Agent Design](#7-ai-agent-design)
8. [API Design](#8-api-design)
9. [Deployment Plan (Free Tier)](#9-deployment-plan-free-tier)
10. [Build Roadmap](#10-build-roadmap)
11. [Benchmark Strategy](#11-benchmark-strategy)
12. [Interview Positioning](#12-interview-positioning)
---
 
## 1. Vision & Positioning
 
**LeadMind** is an end-to-end autonomous AI outbound agent. It finds leads, enriches them with behavioral signals, writes genuinely personalized emails, executes multi-step sequences, and handles replies autonomously — including multi-turn conversations — without human intervention.
 
It is architecturally similar to Artisan's Ava, but closes **three real product gaps** that exist in Ava today:
 
| Gap in Ava | How LeadMind Fixes It |
|---|---|
| Personalization is enrichment-based (formulaic) | Behavioral Personalization Engine — personalize on what prospects actually say and think |
| Reply handling degrades after turn 2 | Stateful Multi-Turn Reply Handler — explicit conversation memory |
| No revenue feedback loop (only reply rate tracked) | Meeting-to-Revenue Tracker — closes the loop from booked meeting to outcome |
 
**Target audience for this project:** Artisan's engineering team, specifically Ming Li (CTO) and Jaspar Carmichael-Jack (CEO).
 
---
 
## 2. What Artisan Does vs What LeadMind Does Better
 
```
ARTISAN AVA                              LEADMIND
────────────────────────────────────     ────────────────────────────────────────────
Enrichment-based personalization    →    Behavioral personalization (LinkedIn posts,
  "I saw your Series B"                    opinion mining, semantic hook matching)
 
Reply handler breaks at turn 3      →    Stateful ConversationState object; handles
  (routes to human)                         5+ turns with full coherence
 
Tracks: reply rate only             →    Revenue feedback loop: reply → meeting →
  (open-ended optimization loop)            outcome → model recalibration signal
 
Fixed prompt templates              →    Dynamic few-shot injection from your own
                                          high-reply history
 
GPT-4o required (paid)              →    Groq (free) + Ollama (free) + HuggingFace
                                          (free) — zero LLM cost
```
 
---
 
## 3. System Architecture
 
```
┌─── Frontend (Next.js 14, Vercel free tier) ──────────────────────────────────┐
│   Lead Browser | Campaign Builder | Conversation View | Analytics Dashboard  │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ REST + WebSocket (Socket.io)
┌─── API Layer (FastAPI, Railway free tier) ────────────────────────────────────┐
│   /leads  /campaigns  /sequences  /replies  /analytics  /conversations        │
└────────────┬──────────────────────────────────────────────────────────────────┘
             │ Enqueue jobs (Redis Queue / RQ)
┌─── Worker Layer ──────────────────────────────────────────────────────────────┐
│   enrichment_worker    → Scraperapi + NewsAPI + LinkedIn scrape               │
│   embedding_worker     → HuggingFace sentence-transformers (local)            │
│   email_gen_worker     → Groq (Llama 3.1 70B free) / Ollama fallback         │
│   sequence_worker      → Schedule + rate-limit + send campaign steps          │
│   reply_worker         → IMAP poll → classify → generate → update state       │
│   revenue_worker       → Track meeting outcome → feed back to scorer          │
└────────────┬──────────────────────────────────────────────────────────────────┘
             │
    ┌────────┼────────────────────┐
    │        │                   │
Postgres   Redis            Qdrant (free)
+ pgvector  (queue+cache)   (vector DB — local)
```
 
**Key design principles:**
- **Async-first**: every LLM call and enrichment call is queued, never synchronous in the request path
- **Free-tier deployable**: the entire stack runs on Railway free + Vercel free + local Qdrant
- **Model-agnostic**: LLM interface abstracted — swap Groq → Ollama → HuggingFace inference without code changes
- **State-explicit**: conversation state is a structured DB record, not just thread history in the prompt
---
 
## 4. Tech Stack (100% Free)
 
| Layer | Technology | Free Tier Details |
|---|---|---|
| **Frontend** | Next.js 14 + Tailwind + Recharts | Vercel free — unlimited personal projects |
| **API** | FastAPI (Python 3.11) | Railway free — 500 hours/month |
| **Task Queue** | Redis Queue (RQ) + Redis | Redis Cloud free — 30MB, sufficient for queue |
| **Primary DB** | PostgreSQL + pgvector extension | Supabase free — 500MB, 2 projects |
| **Vector DB** | Qdrant (self-hosted via Docker) | Free, runs locally or on Railway |
| **LLM (primary)** | Groq API — Llama 3.1 70B | Free tier: 14,400 requests/day, 30 RPM |
| **LLM (fallback)** | Ollama — Llama 3.1 8B | Fully local, zero cost |
| **LLM (classification)** | Groq — Llama 3.1 8B (faster, cheaper) | Free tier included |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) | Local, zero cost |
| **Lead data** | Apollo.io free tier | 50 exports/month free |
| **LinkedIn posts** | Scraperapi free tier | 1,000 API calls/month free |
| **Company news** | NewsAPI free tier | 100 requests/day free |
| **Email sending** | Resend free tier | 3,000 emails/month free |
| **Calendar** | Cal.com API (open source) | Free self-hosted or free cloud plan |
| **Deployment (BE)** | Railway free | 500 compute hours/month |
| **Deployment (FE)** | Vercel free | Unlimited |
 
> **Total monthly cost: $0.00**
> The only exception: if you exceed Groq's free tier (14,400 req/day), Ollama local fallback kicks in automatically. No credit card required for the entire stack.
 
### LLM Model Strategy
 
```
Task                    Model                   Why
────────────────────────────────────────────────────────────────────────
Email generation        Groq / Llama 3.1 70B    Best free quality for long-form
Reply generation        Groq / Llama 3.1 70B    Multi-turn coherence
State extraction        Groq / Llama 3.1 8B     Fast structured output (JSON)
Intent classification   Groq / Llama 3.1 8B     Low-latency, cheap
Hallucination check     Groq / Llama 3.1 8B     Verification pass
Embeddings              all-MiniLM-L6-v2        Local, 384-dim, fast, free
```
 
---
 
## 5. Data Models
 
```sql
-- Prospects
CREATE TABLE prospects (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         TEXT UNIQUE NOT NULL,
    name          TEXT,
    first_name    TEXT,
    title         TEXT,
    company       TEXT,
    linkedin_url  TEXT,
    icp_score     FLOAT,                    -- 0-1 cosine similarity to ICP
    urgency_score FLOAT,                    -- weighted signal sum
    enrichment    JSONB,                    -- raw enrichment data from all sources
    signal_flags  TEXT[],                  -- ['funding', 'hiring_sdrs', 'job_change']
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
 
-- Campaigns
CREATE TABLE campaigns (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    icp_description TEXT,                  -- used for embedding ICP match
    value_prop      TEXT,                  -- used for behavioral hook retrieval
    tone            TEXT DEFAULT 'concise', -- concise | friendly | direct | formal
    banned_phrases  TEXT[],
    steps           JSONB,                 -- [{channel, delay_days, goal}, ...]
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
 
-- Campaign Enrollments
CREATE TABLE enrollments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prospect_id     UUID REFERENCES prospects(id),
    campaign_id     UUID REFERENCES campaigns(id),
    state           TEXT DEFAULT 'enrolled',  -- enrolled|contacted|replied|booked|cold|unsubscribed
    current_step    INT DEFAULT 0,
    variant_bucket  TEXT,                  -- 'behavioral' | 'standard' (for A/B)
    enrolled_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(prospect_id, campaign_id)
);
 
-- Emails Sent
CREATE TABLE emails (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enrollment_id  UUID REFERENCES enrollments(id),
    step_num       INT,
    subject        TEXT,
    body           TEXT,
    hook_type      TEXT,                   -- 'behavioral' | 'standard' | 'funding' | 'hiring'
    hook_source    TEXT,                   -- the post or signal that generated the hook
    hook_score     FLOAT,                  -- relevance score of behavioral hook (0-1)
    sent_at        TIMESTAMPTZ,
    opened_at      TIMESTAMPTZ,
    replied_at     TIMESTAMPTZ
);
 
-- Inbound Replies
CREATE TABLE replies (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id          UUID REFERENCES emails(id),
    prospect_id       UUID REFERENCES prospects(id),
    body              TEXT,
    intent            TEXT,               -- INTERESTED|OBJECTION_*|QUESTION|UNSUBSCRIBE|OOO|ANGRY|REFERRAL
    intent_confidence FLOAT,
    received_at       TIMESTAMPTZ,
    response_sent     BOOLEAN DEFAULT FALSE,
    response_body     TEXT,
    turn_number       INT
);
 
-- *** DIFFERENTIATOR #2: Explicit Conversation State ***
CREATE TABLE conversation_states (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prospect_id           UUID REFERENCES prospects(id),
    campaign_id           UUID REFERENCES campaigns(id),
    stage                 TEXT DEFAULT 'exploring',  -- exploring|objecting|scheduling|escalated|closed
    open_questions        TEXT[],                    -- questions not yet answered
    objections_raised     TEXT[],                    -- all objections seen
    objections_addressed  TEXT[],                    -- objections already handled
    commitments_made      TEXT[],                    -- 'will send case study', etc.
    prospect_pain_signal  TEXT,                      -- extracted from their own words
    prior_claims          JSONB,                     -- facts stated (pricing, timelines) for consistency check
    turn_count            INT DEFAULT 0,
    escalated             BOOLEAN DEFAULT FALSE,
    updated_at            TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(prospect_id, campaign_id)
);
 
-- *** DIFFERENTIATOR #1: Behavioral Post Embeddings (pgvector) ***
CREATE TABLE post_embeddings (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prospect_id  UUID REFERENCES prospects(id),
    post_text    TEXT,
    post_date    DATE,
    embedding    vector(384),             -- all-MiniLM-L6-v2 output dimension
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON post_embeddings USING ivfflat (embedding vector_cosine_ops);
 
-- *** DIFFERENTIATOR #3: Revenue Feedback Loop ***
CREATE TABLE meeting_outcomes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prospect_id     UUID REFERENCES prospects(id),
    meeting_at      TIMESTAMPTZ,
    outcome         TEXT,                -- showed_up|no_show|qualified|unqualified|closed|lost
    deal_value      NUMERIC,
    loss_reason     TEXT,                -- 'not_budget'|'not_timing'|'competitor'|'not_interested'
    recorded_at     TIMESTAMPTZ DEFAULT NOW()
);
 
-- Analytics Events
CREATE TABLE events (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type        TEXT,                    -- email_sent|opened|replied|meeting_booked|meeting_outcome
    prospect_id UUID REFERENCES prospects(id),
    campaign_id UUID REFERENCES campaigns(id),
    metadata    JSONB,
    occurred_at TIMESTAMPTZ DEFAULT NOW()
);
```
 
---
 
## 6. Feature Specifications
 
---
 
### F1: Lead Discovery & ICP Matching
 
**Goal:** Given a natural-language ICP description, find and score matching leads.
 
**Flow:**
1. User inputs ICP description: *"VP of Sales at B2B SaaS companies, 50-500 employees, US-based, using Salesforce"*
2. ICP description is embedded via `all-MiniLM-L6-v2`
3. Apollo.io API queried with structured filters (title, industry, company size, geo)
4. Each returned lead profile is embedded (title + company + bio concatenated)
5. Cosine similarity between ICP embedding and lead embedding → `icp_score`
6. Results sorted by `icp_score`, displayed in Lead Browser UI
**Implementation:**
```python
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
 
model = SentenceTransformer('all-MiniLM-L6-v2')
 
def score_lead_icp(icp_description: str, lead: dict) -> float:
    lead_text = f"{lead['title']} at {lead['company']}. {lead.get('bio', '')}"
    icp_emb = model.encode([icp_description])
    lead_emb = model.encode([lead_text])
    return float(cosine_similarity(icp_emb, lead_emb)[0][0])
```
 
**Data out:** `prospects` table row with `icp_score`
 
---
 
### F2: Enrichment Pipeline
 
**Goal:** Enrich each lead with behavioral signals, company news, and LinkedIn activity data.
 
**Waterfall (free sources only):**
 
| Priority | Source | Fields | Free Limit |
|---|---|---|---|
| 1 | Apollo.io | email, title, company size, phone | 50/month |
| 2 | Scraperapi → LinkedIn | recent posts (last 30), activity score | 1,000/month |
| 3 | NewsAPI | company funding/news mentions (last 90d) | 100/day |
| 4 | Scraperapi → company site | job postings (hiring SDRs?), tech stack hints | included |
 
**Signal Detection Logic:**
```python
SIGNAL_PATTERNS = {
    "hiring_sdrs":   ["BDR", "SDR", "Sales Development", "Account Executive"],
    "job_change":    ["started new position", "excited to join", "thrilled to announce"],
    "fundraising":   ["Series A", "Series B", "seed round", "raised"],
    "evaluating":    ["looking for", "recommendation", "which tool", "anyone use"],
}
 
def detect_signals(posts: list[str], news: list[str]) -> list[str]:
    all_text = " ".join(posts + news).lower()
    return [sig for sig, keywords in SIGNAL_PATTERNS.items()
            if any(kw.lower() in all_text for kw in keywords)]
```
 
**Urgency Score Calculation:**
```python
SIGNAL_WEIGHTS = {
    "hiring_sdrs":  0.9,
    "job_change":   0.8,
    "fundraising":  0.85,
    "evaluating":   0.95,
    "recent_post":  0.3,    # active on LinkedIn
}
 
def compute_urgency_score(signals: list[str]) -> float:
    return min(1.0, sum(SIGNAL_WEIGHTS.get(s, 0) for s in signals))
```
 
**Async execution:** Each lead's enrichment is queued as an RQ job. Workers run per source in parallel. `enrichment_data` JSONB stores raw results. Coverage % logged per lead.
 
---
 
### F3: Behavioral Personalization Engine *(Gap Fix #1 — KEY DIFFERENTIATOR)*
 
**Problem being solved:** Ava personalizes based on job title and funding data. Every AI BDR tool does this. Prospects in 2026 receive 5–10 AI-written emails per day and recognize the pattern instantly. *"I saw you raised a Series B"* is now dead.
 
Real personalization means referencing what the prospect **actually said, argued, or publicly cares about** — their real opinions, not their metadata.
 
**Architecture:**
 
```
LinkedIn Posts (Scraperapi)
        ↓
  Embed each post (all-MiniLM-L6-v2, dim=384)
        ↓
  Store in pgvector indexed by prospect_id
        ↓
[At email write time]
  Embed campaign value_prop
        ↓
  Query pgvector → top 3 semantically similar posts
        ↓
  LLM: generate 1-2 sentence hook referencing real post
        ↓
  Hallucination verifier: does hook accurately reflect post?
        ↓
  Relevance score ≥ 0.60 → use behavioral hook
  Relevance score < 0.60 → fall back to signal-based hook
```
 
**Core implementation:**
 
```python
async def index_prospect_posts(prospect_id: str, posts: list[dict]):
    """Run at enrichment time. Embed and store all posts."""
    for post in posts:
        embedding = model.encode(post["text"]).tolist()
        await db.execute("""
            INSERT INTO post_embeddings (prospect_id, post_text, post_date, embedding)
            VALUES ($1, $2, $3, $4)
        """, prospect_id, post["text"], post["date"], embedding)
 
 
async def generate_behavioral_hook(
    prospect_id: str,
    value_prop: str,
    campaign_context: str
) -> tuple[str | None, float]:
    """
    Returns: (hook_text, relevance_score) or (None, 0.0) if no good hook found.
    """
    vp_embedding = model.encode(value_prop).tolist()
 
    # Query top-3 semantically similar posts from pgvector
    rows = await db.fetch("""
        SELECT post_text, post_date,
               1 - (embedding <=> $1::vector) AS similarity
        FROM post_embeddings
        WHERE prospect_id = $2
        ORDER BY embedding <=> $1::vector
        LIMIT 3
    """, vp_embedding, prospect_id)
 
    if not rows:
        return None, 0.0
 
    top_post = rows[0]
    if top_post["similarity"] < 0.35:       # not even loosely related
        return None, 0.0
 
    # Generate hook via Groq (Llama 3.1 70B)
    hook = await llm.complete(
        system="You write personalized email openers. Be specific, natural, never sycophantic.",
        user=f"""
LinkedIn post by prospect (written by them, dated {top_post['post_date']}):
"{top_post['post_text']}"
 
Product we're selling: {value_prop}
 
Write ONE sentence (max 25 words) that:
- References something specific from their post (a word, stance, or question they raised)
- Connects naturally to why we're reaching out
- Sounds like a human wrote it, not a bot
- NEVER starts with "I saw your post" or "I noticed"
 
Output ONLY the sentence, nothing else.
"""
    )
 
    # Hallucination verification pass
    verified = await llm.complete(
        system="You are a fact checker. Answer only YES or NO.",
        user=f"""
Does this email opener accurately reflect something the person said in their LinkedIn post?
 
Post: "{top_post['post_text']}"
Opener: "{hook}"
 
Does the opener reference something genuinely present in the post? YES or NO.
"""
    )
 
    if "NO" in verified.upper():
        return None, 0.0
 
    # Score relevance (0-1)
    score = top_post["similarity"]
    return hook if score >= 0.60 else None, score
 
 
async def get_best_hook(
    prospect_id: str, value_prop: str, signals: list[str], enrichment: dict
) -> tuple[str, str]:
    """
    Returns: (hook_text, hook_type)
    Priority: behavioral > signal-based > generic
    """
    behavioral_hook, score = await generate_behavioral_hook(prospect_id, value_prop, "")
    if behavioral_hook:
        return behavioral_hook, "behavioral"
 
    # Signal-based fallback
    if "hiring_sdrs" in signals:
        return f"Noticed {enrichment['company']} is building out the sales team right now.", "hiring"
    if "fundraising" in signals:
        return f"Saw the recent news from {enrichment['company']} — congrats on the raise.", "funding"
    if "job_change" in signals:
        return f"Congrats on the new role at {enrichment['company']}.", "job_change"
 
    # Generic fallback
    return f"Reaching out because we work with a lot of {enrichment['title']}s in {enrichment['industry']}.", "generic"
```
 
**A/B Test Assignment:**
At enrollment, each prospect is randomly assigned to `variant_bucket`:
- `behavioral` — uses behavioral hook if score ≥ 0.60, else signal-based
- `standard` — always uses signal-based hook (control group)
Open rate and reply rate tracked per `hook_type`. This generates the benchmark chart.
 
---
 
### F4: Email Generation with A/B Variants
 
**Goal:** Generate 3 subject + body variants per lead, personalized via behavioral hook.
 
**Prompt Architecture:**
 
```python
SYSTEM_PROMPT = """
You are writing a cold email on behalf of {sender_name} at {company_name}.
Tone: {tone}
Value proposition: {value_prop}
Never use: {banned_phrases}
Keep body under 150 words. No fluff. No "I hope this finds you well."
""".strip()
 
USER_PROMPT = """
Prospect: {first_name} {last_name}, {title} at {company}
Opening hook: {hook}
Signals: {signal_summary}
Email step: {step_num} of {total_steps} (Goal: {step_goal})
 
Generate 3 email variants. For each output:
VARIANT_N:
SUBJECT: <subject line, max 8 words, no clickbait>
BODY: <email body, 100-150 words, includes hook, ends with 1 specific CTA>
---
""".strip()
```
 
**Guardrails (applied post-generation):**
- Spam word filter: regex against known spam trigger words
- Length check: body > 200 words → regenerate with `max_words` instruction
- Factual claim check: any specific claim about the company verified against `enrichment` data
**Cost:** $0.00 (Groq free tier). Prompt caching: system prompt is static per campaign — identical across all prospects in the same campaign. ~60% token savings.
 
---
 
### F5: Campaign Sequence Engine
 
**Goal:** Orchestrate multi-step email sequences with durable scheduling, rate limiting, and reply detection.
 
**Sequence Config (stored in `campaigns.steps` JSONB):**
```json
[
  {"step": 1, "channel": "email", "delay_days": 0,  "goal": "awareness"},
  {"step": 2, "channel": "email", "delay_days": 3,  "goal": "value_add"},
  {"step": 3, "channel": "email", "delay_days": 7,  "goal": "meeting_ask"},
  {"step": 4, "channel": "email", "delay_days": 12, "goal": "breakup"}
]
```
 
**Rate Limiting (Redis token bucket):**
```python
async def acquire_send_slot(domain: str, channel: str) -> bool:
    """Returns True if send is allowed, False if rate-limited."""
    key = f"rate:{channel}:{domain}:{date.today()}"
    limits = {"email": 50, "linkedin": 25}
    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, 86400)  # reset at midnight
    return current <= limits[channel]
```
 
**Reply Detection (IMAP polling every 5 min):**
```python
async def poll_inbox():
    with imaplib.IMAP4_SSL(IMAP_HOST) as imap:
        imap.login(EMAIL, PASSWORD)
        imap.select("INBOX")
        _, message_ids = imap.search(None, "UNSEEN")
        for mid in message_ids[0].split():
            email_data = parse_email(imap.fetch(mid, "(RFC822)"))
            if enrollment := await match_to_enrollment(email_data["thread_id"]):
                await cancel_pending_jobs(enrollment.id)   # stop sequence
                await queue_reply_handler(enrollment, email_data["body"])
```
 
**State Machine:**
```
ENROLLED
  └─→ CONTACTED (email sent)
        └─→ REPLIED
              ├─→ MEETING_BOOKED  (terminal — success)
              ├─→ OBJECTING → REBUTTING → COLD  (terminal)
              ├─→ ESCALATED (human takeover)
              └─→ UNSUBSCRIBED  (terminal — global suppression)
```
 
---
 
### F6: Stateful Multi-Turn Reply Handler *(Gap Fix #2 — KEY DIFFERENTIATOR)*
 
**Problem being solved:** Ava's reply handling breaks after 2 exchanges. Thread history stuffed into a prompt context is not conversation understanding. The AI re-introduces itself, repeats already-addressed objections, or gives inconsistent answers on pricing and timelines.
 
Root cause: **no explicit conversation state**. Context window ≠ memory.
 
**The Fix: ConversationState as a first-class database object.**
 
After every inbound reply, a structured extraction LLM call updates the `conversation_states` record. Reply generation reads from this structured state — not just raw thread history.
 
**State Extraction (runs after every reply):**
```python
async def extract_and_update_state(
    reply_text: str,
    state: ConversationState,
    prior_thread: list[dict]
) -> ConversationState:
    """LLM extracts structured facts from inbound reply and updates state."""
 
    extraction = await llm.complete(
        system="You extract structured conversation facts from sales email replies. Output only valid JSON.",
        user=f"""
Previous state: {state.model_dump_json()}
New inbound reply: "{reply_text}"
 
Extract and return a JSON object with these fields:
{{
  "new_open_questions": [],       // new questions the prospect asked (not yet answered)
  "new_objections": [],           // new objections raised
  "resolved_objections": [],      // objections that this reply resolved
  "new_commitments": [],          // things WE committed to in our last reply that must be followed through
  "pain_signal": "",              // strongest pain point expressed in their words (or null)
  "stage": "",                    // one of: exploring, objecting, scheduling, escalated
  "should_escalate": false        // true if: legal language, anger, >4 turns, enterprise account
}}
Output ONLY the JSON object. No explanation.
"""
    )
 
    update = json.loads(extraction)
 
    state.open_questions      = [q for q in state.open_questions
                                   if q not in update.get("resolved_objections", [])]
    state.open_questions     += update.get("new_open_questions", [])
    state.objections_raised  += update.get("new_objections", [])
    state.objections_addressed += update.get("resolved_objections", [])
    state.commitments_made   += update.get("new_commitments", [])
    if update.get("pain_signal"):
        state.prospect_pain_signal = update["pain_signal"]
    state.stage               = update.get("stage", state.stage)
    state.turn_count         += 1
 
    await db.save_conversation_state(state)
    return state
```
 
**Reply Generation (reads from structured state):**
```python
async def generate_reply(
    reply_text: str,
    state: ConversationState,
    thread: list[dict],
    enrichment: dict
) -> str:
 
    if state.turn_count > 4 or state.escalated:
        await escalate_to_human(state, thread)
        return None
 
    response = await llm.complete(
        system="""You are a professional sales rep continuing an email conversation.
Be concise, warm, and specific. Never repeat yourself.""",
        user=f"""
Thread summary (structured):
- Current stage: {state.stage}
- Open questions (MUST address ALL of these): {state.open_questions}
- Objections raised: {state.objections_raised}
- Already addressed objections (DO NOT repeat rebuttals for these): {state.objections_addressed}
- Commitments we made (follow through on these): {state.commitments_made}
- Prospect's pain signal (use their words, not assumptions): {state.prospect_pain_signal}
- Turn {state.turn_count} of conversation
 
Full thread:
{format_thread(thread)}
 
Latest reply from prospect:
"{reply_text}"
 
Write a reply that:
1. Addresses EVERY open question in the list
2. Does NOT re-raise addressed objections
3. Follows through on any commitments made
4. If stage is 'scheduling': propose 2-3 specific meeting times
5. Is under 150 words
"""
    )
 
    # Consistency check — verify no factual contradictions
    if state.prior_claims:
        consistent = await verify_consistency(response, state.prior_claims)
        if not consistent:
            response = await fix_consistency(response, state.prior_claims)
 
    return response
```
 
**Escalation Triggers:**
- `turn_count > 4`
- Legal language detected (`cease`, `lawyer`, `litigation`)
- Intent classified as `ANGRY`
- `should_escalate = True` from extraction call
On escalation: send Slack webhook with full conversation summary (3-bullet summary generated by LLM).
 
**Benchmark target:** Show conversation quality score (question coverage rate, no repeated objections, factual consistency) across turns 1–6, comparing stateful vs stateless handler. Expected: stateless degrades sharply at turn 3; stateful maintains near-constant quality.
 
---
 
### F7: Revenue Feedback Loop *(Gap Fix #3 — UNIQUE to LeadMind)*
 
**Problem being solved:** Artisan tracks reply rate and meeting booked rate. But there is no signal from what happens after the meeting. If 9 out of 10 booked meetings no-show or were never truly qualified, the lead scoring model and reply handler never learn. Optimization is blind past the "meeting booked" event.
 
**This is the difference between a marketing metric and a business metric.**
 
**Implementation:**
 
After a meeting is logged, the user (or a Slack bot prompt) records the outcome:
- `showed_up` / `no_show`
- `qualified` / `unqualified`
- `closed` / `lost`
- `loss_reason`: `not_budget` | `not_timing` | `competitor` | `wrong_person`
These outcomes feed back into two systems:
 
**1. Lead scorer recalibration:**
```python
async def recalibrate_lead_score_weights(
    outcome: str,
    prospect: dict,
    signals: list[str]
):
    """
    Adjust signal weights based on meeting outcomes.
    If prospects with 'hiring_sdrs' signal have 80% show-up rate → weight stays high.
    If 'fundraising' signal prospects mostly no-show → reduce weight.
    Stored in Redis as rolling averages per signal type.
    """
    key = f"signal_perf:{outcome}:{signal}"
    for signal in signals:
        await redis.lpush(key, 1 if outcome in ["qualified", "closed"] else 0)
        await redis.ltrim(key, 0, 99)  # rolling window of last 100 outcomes
```
 
**2. Reply quality scorer:**
Track whether prospects with high conversation state coherence (stateful handler) have better meeting show-up rates. This closes the loop from AI design decision → revenue impact.
 
**Dashboard widget:** "Lead-to-Revenue Funnel" — shows reply rate → meeting rate → show-up rate → qualified rate → close rate. This is the chart that proves LeadMind optimizes for revenue, not just vanity metrics.
 
---
 
### F8: Meeting Booking
 
**Goal:** Autonomously book meetings from INTERESTED replies.
 
**Flow:**
1. Reply classified as `INTERESTED`
2. Cal.com API called → fetch next 3 available slots in prospect's likely timezone
3. Reply generated with 3 specific times embedded (e.g., "I have Tuesday 2pm, Wednesday 10am, or Thursday 3pm EST — any work?")
4. On prospect's confirmation reply → Cal.com API creates booking
5. Google Calendar invite sent (via Cal.com integration)
6. `meeting_outcomes` record created with `outcome = NULL` (pending)
7. Slack webhook notification fired
**Timezone detection:** Inferred from prospect's `enrichment.country` and `enrichment.city` via `pytz`.
 
---
 
### F9: Analytics Dashboard
 
**Goal:** Surface the metrics that matter for a portfolio demo — specifically the two benchmark charts.
 
**Key views:**
 
**1. Campaign Overview**
- Total sent / open rate / reply rate / positive reply rate / meeting rate
- Trend line by week
**2. Behavioral Hook Lift (THE key chart)**
- Side-by-side bar chart: `behavioral` hook vs `standard` hook reply rates
- Sample size label + statistical significance indicator (p-value)
- This is the chart you show in every interview
**3. Conversation Quality by Turn (SECOND key chart)**
- Line chart: turns 1–6 on X axis
- Metrics: question coverage rate, objection repeat rate, factual consistency score
- Two lines: stateful handler vs stateless handler (from benchmark test harness)
**4. Revenue Funnel**
- Funnel chart: leads found → enriched → contacted → replied → meeting booked → showed up → qualified → closed
**5. Lead Browser**
- Table: leads with icp_score, urgency_score, signals, enrollment status
- Filter by campaign, signal type, state
**Tech:** Next.js 14 + Recharts + Tailwind. All data from Postgres aggregation queries via FastAPI.
 
---
 
## 7. AI Agent Design
 
LeadMind uses a **multi-worker agent pattern** — specialized workers orchestrated by a job queue, not a monolithic LLM call.
 
```
┌──────────────────────────────────────────────────────────┐
│                    Job Queue (RQ + Redis)                 │
│                                                          │
│  enrichment_job → embedding_job → email_gen_job          │
│  sequence_job → reply_detect_job → reply_gen_job         │
│  outcome_record_job → score_recal_job                    │
└──────────────────────────────────────────────────────────┘
 
Agent Roles:
┌─────────────────┬──────────────────┬───────────────────────────┐
│ Agent           │ Model            │ Responsibility             │
├─────────────────┼──────────────────┼───────────────────────────┤
│ Writer Agent    │ Groq Llama 70B   │ Email generation (3 vars)  │
│ Hook Agent      │ Groq Llama 70B   │ Behavioral hook + verify   │
│ State Extractor │ Groq Llama 8B    │ Structured state updates   │
│ Reply Agent     │ Groq Llama 70B   │ Multi-turn reply gen       │
│ Classifier      │ Groq Llama 8B    │ Intent classification      │
│ Embedder        │ all-MiniLM local │ Post + ICP embeddings      │
│ Scorer          │ Rule-based       │ Signal weighting, urgency  │
└─────────────────┴──────────────────┴───────────────────────────┘
```
 
**LLM Interface (model-agnostic abstraction):**
```python
class LLMClient:
    """Swappable LLM backend — Groq, Ollama, or HuggingFace."""
 
    async def complete(self, system: str, user: str, json_mode: bool = False) -> str:
        try:
            return await self._groq_complete(system, user, json_mode)
        except RateLimitError:
            return await self._ollama_complete(system, user)   # local fallback
 
    async def _groq_complete(self, system, user, json_mode) -> str:
        # Groq API call (free tier)
        ...
 
    async def _ollama_complete(self, system, user) -> str:
        # Local Ollama (Llama 3.1 8B) — zero cost, slower
        ...
```
 
---
 
## 8. API Design
 
```
GET    /api/leads                          # search + filter leads
POST   /api/leads/discover                 # trigger ICP-based Apollo search
POST   /api/leads/{id}/enrich             # queue enrichment job
 
GET    /api/campaigns                      # list campaigns
POST   /api/campaigns                      # create campaign
GET    /api/campaigns/{id}/enrollments     # list enrollments + states
 
POST   /api/campaigns/{id}/enroll         # enroll prospect(s) in campaign
DELETE /api/enrollments/{id}              # unenroll / stop sequence
 
GET    /api/conversations/{prospect_id}    # full thread + state
POST   /api/conversations/{id}/escalate   # manual human takeover
 
GET    /api/analytics/overview            # aggregate campaign stats
GET    /api/analytics/hook-lift           # behavioral vs standard A/B data
GET    /api/analytics/conversation-quality # turn-by-turn coherence scores
GET    /api/analytics/revenue-funnel      # end-to-end funnel metrics
 
POST   /api/meetings/{id}/outcome         # record meeting outcome
```
 
---
 
## 9. Deployment Plan (Free Tier)
 
```
Service          Platform            Free Tier Limit      Notes
────────────────────────────────────────────────────────────────────────
Frontend         Vercel              Unlimited             Deploy main branch
FastAPI          Railway             500 hrs/month         1 service, always-on
RQ Workers       Railway             500 hrs/month         2nd service, same project
PostgreSQL       Supabase            500MB, 2 projects     pgvector enabled by default
Redis            Redis Cloud         30MB                  Sufficient for queue + cache
Qdrant           Railway (Docker)    Runs as 3rd service   Or run locally for demo
Ollama (local)   Local machine       Free                  Fallback when Groq rate-limited
```
 
**One-command local dev setup:**
```bash
git clone https://github.com/yourname/leadmind
cd leadmind
docker-compose up -d          # Postgres + pgvector + Redis + Qdrant
pip install -r requirements.txt
npm install
cp .env.example .env          # fill in Groq API key (free), Apollo key (free), etc.
make dev                      # starts FastAPI + RQ workers + Next.js
```
 
---
 
## 10. Build Roadmap
 
### Phase 1: Core Data Pipeline (Weeks 1–3)
 
| Week | Task | Deliverable |
|---|---|---|
| 1 | Project scaffold (FastAPI + Next.js + Postgres + pgvector + RQ + Redis) | Local dev environment running |
| 1 | Apollo.io lead discovery integration. Store leads in Postgres. | Lead search working |
| 1 | Scraperapi LinkedIn post scraper. Parse + store posts. | Raw posts in DB |
| 2 | Embedding pipeline: all-MiniLM-L6-v2 local. Index posts in pgvector. | Vector index populated |
| 2 | ICP embedding + cosine similarity lead scoring | icp_score computed per lead |
| 2 | Signal detection (hiring, funding, job change, evaluating) + urgency score | Signal flags + urgency_score |
| 3 | NewsAPI company news enrichment | Enrichment waterfall complete |
| 3 | Basic email generation (Groq / Llama 3.1 70B). 3 variants. | Emails generated end-to-end |
| 3 | **MILESTONE:** Given ICP → find 10 leads → enrich → generate 3 email variants each | ✅ |
 
### Phase 2: Behavioral Engine + Sequence Runner (Weeks 4–6)
 
| Week | Task | Deliverable |
|---|---|---|
| 4 | Behavioral hook generator: embed value prop → query pgvector → generate hook | Hook generation working |
| 4 | Hallucination verifier (second LLM pass). Relevance scorer. Fallback logic. | Hook quality gate working |
| 4 | A/B variant assignment at enrollment (`behavioral` vs `standard` bucket) | A/B framework in place |
| 5 | Campaign sequence engine: RQ delayed jobs per step. Rate limiter (Redis). | Sequences firing correctly |
| 5 | IMAP reply polling (every 5 min). Detect reply → cancel pending jobs. | Reply detection working |
| 6 | Intent classifier (Groq Llama 8B, 12 labels, structured JSON output) | Classification accurate |
| 6 | **MILESTONE:** Run real 3-step email sequence to 10 test prospects. Handle replies. | ✅ |
 
### Phase 3: Stateful Reply Handler + Revenue Loop (Weeks 7–8)
 
| Week | Task | Deliverable |
|---|---|---|
| 7 | ConversationState DB model + state extraction LLM call | State correctly extracted |
| 7 | Multi-turn reply generator with structured state injection | 5-turn coherent conversations |
| 7 | Consistency checker (verify no factual contradictions) | Consistency check working |
| 7 | Escalation triggers (turn count, legal language, ANGRY) + Slack webhook | Escalation firing |
| 8 | Cal.com meeting booking integration. Timezone detection. | Meetings booked autonomously |
| 8 | Revenue outcome recording. Signal weight recalibration. | Revenue loop closed |
| 8 | **MILESTONE:** Full autonomous cycle: lead → enrich → sequence → reply → meeting → outcome | ✅ |
 
### Phase 4: Dashboard + Benchmarks (Weeks 9–10)
 
| Week | Task | Deliverable |
|---|---|---|
| 9 | Next.js analytics dashboard. All metric views. Recharts graphs. | Dashboard live |
| 9 | Behavioral Hook Lift chart (A/B result visualization) | Key benchmark chart |
| 9 | Conversation Quality by Turn chart (stateful vs stateless) | Second benchmark chart |
| 9 | Revenue Funnel chart | Third key chart |
| 10 | Run real A/B benchmark (50+ sends per variant). Document results. | Real lift numbers |
| 10 | Build stateless handler test harness. Score turns 1–6. Compare to stateful. | Degradation curve documented |
| 10 | README: system diagram (Mermaid), setup in 5 commands, benchmark table, cost breakdown | Complete GitHub README |
| 10 | Deploy to Vercel + Railway. Pre-load 10 real leads with real data. | Live demo URL |
| 10 | Record 5-minute Loom walkthrough | Demo video |
| 10 | **MILESTONE:** Live demo, real benchmarks, complete GitHub README | ✅ |
 
### Phase 5: Outreach (Weeks 11–12)
 
| Week | Task |
|---|---|
| 11 | Write case study blog post. Publish on Medium/personal site. Post to LinkedIn. |
| 11 | Send direct outreach to Jaspar (CEO) and Ming (CTO) on LinkedIn |
| 12 | Apply formally via Artisan careers page. Follow up. Prepare for technical interview. |
 
---
 
## 11. Benchmark Strategy
 
Two benchmarks are essential for the portfolio. These are not synthetic — they use real sends and real conversations.
 
### Benchmark A: Behavioral Hook Lift
 
**Method:**
- Enroll 100 prospects in same campaign (same ICP, same sequence)
- 50 randomly assigned to `behavioral` bucket, 50 to `standard`
- Track reply rate per bucket over 14 days
- Statistical significance: Chi-squared test, p < 0.05
**Expected result to aim for:**
- Standard hook reply rate: ~2.5%
- Behavioral hook reply rate: ~3.5–4.5% (20–80% lift)
- Even 20% lift is meaningful and defensible
**What you show:**
- Bar chart: behavioral vs standard reply rate
- Sample size + p-value label
- Example behavioral hook + the LinkedIn post that generated it
### Benchmark B: Conversation Coherence by Turn
 
**Method:**
- Build a test harness with 10 simulated 6-turn conversations
- Each turn: realistic prospect reply (covering: objection, question, scheduling, pushback)
- Score each AI response on 3 dimensions:
  - **Question coverage rate**: % of open questions answered in the reply (0–1)
  - **Objection repeat rate**: did it repeat an already-addressed objection? (0 = never, 1 = always)
  - **Factual consistency**: did it contradict any prior stated fact? (0 = contradiction, 1 = consistent)
- Run same conversations through: (a) stateful handler, (b) stateless handler (just thread history in prompt)
**Expected result:**
- Stateless: coherence drops sharply at turn 3 (question coverage < 0.5, repeat rate > 0.4)
- Stateful: near-constant quality across all 6 turns (coverage > 0.85, repeat rate < 0.1)
**What you show:**
- Line chart: turns 1–6 on X axis, coherence score on Y axis, two lines (stateful vs stateless)
- This chart is your proof that the technical design decision (explicit state) has measurable impact
---
 
## 12. Interview Positioning
 
### What LeadMind proves to Artisan's engineering team
 
| Claim | Proof |
|---|---|
| You understand Artisan's system deeply | You reverse-engineered the full architecture and identified 3 specific gaps |
| You can ship end-to-end AI systems | Working product — not just a Jupyter notebook or a concept doc |
| Your features are grounded in real problems | Each feature directly addresses a documented weakness in Ava |
| You care about measurement, not just building | Two real benchmarks with methodology and results, not placeholder charts |
| You can work with LLMs professionally | Prompt versioning, hallucination verification, structured output, model routing, cost tracking |
| You understand async distributed systems | RQ workers, rate limiting, IMAP polling, state machines |
 
### Answers prepared for likely interview questions
 
**"Why pgvector instead of Pinecone?"**
> "For a portfolio project, pgvector eliminates an external service dependency and keeps the stack deployable on free tiers. At Artisan's scale — 250M contacts — I'd move to dedicated Pinecone or Qdrant with sharding for better filtering performance and replication guarantees."
 
**"How would you scale this to Artisan's volume?"**
> "Three changes: (1) move task queue from RQ to Kafka for ordered, replayable enrichment streams; (2) partition Postgres by geography/industry and move lead search to Elasticsearch; (3) add prompt caching at the LLM provider level — Groq supports this — for the static system prompt across all leads in a campaign. That 60% token saving compounds enormously at 1M emails/day."
 
**"Your A/B test has N sends — how confident are you?"**
> "At 50 per variant, I'd state the p-value and confidence interval honestly. Direction is clear but I'd want 300+ per variant before making behavioral hooks the default in production. The value of the benchmark is proving the mechanism works, not the exact lift number."
 
**"What would you build next?"**
> "Two things. First: fine-tune Llama 3.1 8B on high-performing email threads (reply rate > 10%) — locally, using LoRA, zero API cost. This is what Artisan should be doing but almost certainly hasn't yet at this scale. Second: extend the revenue feedback loop into the lead scoring model — right now XGBoost weights are hand-tuned; they should be gradient-updated on meeting outcome data weekly."
 
---
 
## Appendix: Environment Variables
 
```bash
# LLM
GROQ_API_KEY=                 # free at console.groq.com
OLLAMA_HOST=http://localhost:11434   # local fallback
 
# Data sources
APOLLO_API_KEY=               # free tier: 50 exports/month
SCRAPERAPI_KEY=               # free tier: 1000 calls/month
NEWS_API_KEY=                 # free tier: 100/day
 
# Email sending
RESEND_API_KEY=               # free tier: 3000/month
IMAP_HOST=imap.gmail.com
IMAP_EMAIL=
IMAP_PASSWORD=                # use Gmail App Password
 
# Calendar
CAL_COM_API_KEY=              # free plan
 
# Database
DATABASE_URL=postgresql://...   # Supabase free
REDIS_URL=redis://...           # Redis Cloud free
 
# Notifications
SLACK_WEBHOOK_URL=             # free
 
# Deployment
RAILWAY_TOKEN=
VERCEL_TOKEN=
```
 
---
 
*LeadMind is a portfolio project built to demonstrate deep understanding of autonomous AI outbound systems. It is not affiliated with Artisan AI.*
