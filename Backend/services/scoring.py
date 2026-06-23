# backend/services/scoring.py
# ICP scoring: how well does a lead match our ideal customer profile?
# Uses semantic similarity — not just keyword matching

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load the model ONCE when this module is imported
# all-MiniLM-L6-v2: small, fast, free, runs locally
# 384 dimensions — good balance of quality vs speed
# First run will download ~80MB model — subsequent runs use cache
print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded.")


def score_lead_icp(icp_description: str, lead: dict) -> float:
    """
    Compute cosine similarity between ICP description and lead profile.

    How it works:
    1. Convert ICP description to a 384-dimensional vector (embedding)
    2. Convert lead profile to another 384-dimensional vector
    3. Measure the angle between them (cosine similarity)
       - Score 1.0 = identical meaning
       - Score 0.0 = completely unrelated
       - Score -1.0 = opposite meaning (rare in practice)

    Real world analogy:
    Imagine every piece of text as a point in 384-dimensional space.
    Similar meanings cluster together.
    Cosine similarity measures how "in the same direction" two points are.
    """

    # Build a text description of the lead from their profile fields
    # More fields = better embedding = more accurate score
    lead_text = " ".join(filter(None, [
        lead.get("title", ""),
        "at",
        lead.get("company", ""),
        lead.get("enrichment", {}).get("industry", ""),
        lead.get("enrichment", {}).get("seniority", ""),
        str(lead.get("enrichment", {}).get("employee_count", "")),
        "employees",
    ]))

    # Encode both texts into embeddings
    # model.encode() returns a numpy array of shape (384,)
    icp_embedding  = model.encode([icp_description])   # shape: (1, 384)
    lead_embedding = model.encode([lead_text])          # shape: (1, 384)

    # cosine_similarity returns a 2D matrix — [0][0] gets the single score
    score = float(cosine_similarity(icp_embedding, lead_embedding)[0][0])

    # Clamp to 0-1 range (cosine can theoretically go negative)
    return max(0.0, min(1.0, score))


def score_batch(icp_description: str, leads: list[dict]) -> list[float]:
    """
    Score multiple leads at once — much faster than one-by-one.
    Sentence transformers are optimized for batch operations.
    """
    icp_embedding = model.encode([icp_description])  # encode ICP once

    lead_texts = [
        " ".join(filter(None, [
            l.get("title", ""),
            "at",
            l.get("company", ""),
            l.get("enrichment", {}).get("industry", ""),
            l.get("enrichment", {}).get("seniority", ""),
        ]))
        for l in leads
    ]

    lead_embeddings = model.encode(lead_texts)   # encode all leads at once

    # Compare ICP embedding against all lead embeddings in one operation
    scores = cosine_similarity(icp_embedding, lead_embeddings)[0]
    return [max(0.0, min(1.0, float(s))) for s in scores]