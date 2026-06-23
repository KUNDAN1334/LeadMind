# backend/services/apollo.py
# Handles all communication with the Apollo.io API
# Apollo is our lead data source — 275M+ professional profiles

import httpx
import os
from dotenv import load_dotenv

load_dotenv()

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
APOLLO_BASE_URL = "https://api.apollo.io/v1"


async def search_people(
    titles: list[str],
    locations: list[str] = None,
    employee_ranges: list[str] = None,
    industries: list[str] = None,
    max_leads: int = 10
) -> list[dict]:
    """
    Search Apollo.io for people matching our ICP filters.
    Returns a list of raw lead dictionaries.

    """

    # Build the search payload
    # Apollo's API uses specific field names — these match their docs exactly
    payload = {
        "api_key": APOLLO_API_KEY,
        "page": 1,
        "per_page": min(max_leads, 25),   # Apollo max per page is 25
        "person_titles": titles,
        "person_locations": locations,
        "organization_num_employees_ranges": employee_ranges,
    }

    if industries:
        payload["organization_industry_tag_ids"] = industries

    # httpx.AsyncClient is like requests.Session but async
    # async with = automatically closes connection when done (even on error)
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{APOLLO_BASE_URL}/mixed_people/search",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        # Raise an exception if Apollo returned an error (4xx, 5xx)
        response.raise_for_status()
        data = response.json()

    # Apollo returns {"people": [...], "pagination": {...}}
    people = data.get("people", [])

    # Clean and normalize each person into our standard format
    leads = []
    for person in people:
        # Apollo's field names don't match ours — we normalize here
        lead = {
            "email": person.get("email") or _build_email(person),
            "name": person.get("name", ""),
            "first_name": person.get("first_name", ""),
            "title": person.get("title", ""),
            "company": person.get("organization", {}).get("name", ""),
            "linkedin_url": person.get("linkedin_url", ""),
            # Store the full raw Apollo data — we might need it later
            "enrichment": {
                "apollo_id": person.get("id"),
                "seniority": person.get("seniority"),
                "departments": person.get("departments", []),
                "city": person.get("city"),
                "state": person.get("state"),
                "country": person.get("country"),
                "employee_count": person.get("organization", {}).get("estimated_num_employees"),
                "industry": person.get("organization", {}).get("industry"),
                "technologies": person.get("organization", {}).get("current_technologies", []),
            }
        }
        # Only include leads with an email — useless without it
        if lead["email"]:
            leads.append(lead)

    return leads


def _build_email(person: dict) -> str | None:
    """
    Apollo sometimes doesn't return email directly.
    Try to construct from available data.
    Returns None if we can't figure it out.
    """
    # Apollo sometimes puts email in contact_emails list
    contact_emails = person.get("contact_emails", [])
    if contact_emails:
        return contact_emails[0].get("email")
    return None


async def get_apollo_usage() -> dict:
    """
    Check how many Apollo credits we've used this month.
    Important: free tier is only 50 exports/month!
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{APOLLO_BASE_URL}/auth/health",
            params={"api_key": APOLLO_API_KEY}
        )
        return response.json()