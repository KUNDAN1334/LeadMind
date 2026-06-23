# backend/services/linkedin.py
# Scrapes LinkedIn posts for a prospect using Scraperapi
# Free tier: 1,000 API calls/month — we fetch max 3 posts per prospect

import httpx
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime, date
import re

load_dotenv()

SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")
SCRAPERAPI_URL = "http://api.scraperapi.com"


async def fetch_linkedin_posts(linkedin_url: str, max_posts: int = 3) -> list[dict]:
    """
    Fetch recent LinkedIn posts for a prospect.

    Returns list of:
    {
        "text": "post content...",
        "date": date object,
        "likes": int,
        "comments": int
    }

    Returns empty list if:
    - No LinkedIn URL provided
    - Scraperapi quota exceeded
    - Profile is private
    - Any error occurs (we never crash the enrichment pipeline)
    """

    if not linkedin_url or not SCRAPERAPI_KEY:
        return []

    # Build the activity URL — LinkedIn posts are at /recent-activity/shares/
    if not linkedin_url.endswith("/"):
        linkedin_url += "/"
    activity_url = f"{linkedin_url}recent-activity/shares/"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Scraperapi wraps our request — it handles:
            # - Rotating IPs (so LinkedIn doesn't block us)
            # - JavaScript rendering (LinkedIn is JS-heavy)
            # - Retry logic
            response = await client.get(
                SCRAPERAPI_URL,
                params={
                    "api_key": SCRAPERAPI_KEY,
                    "url": activity_url,
                    "render": "true",     # enable JavaScript rendering
                    "premium": "false",   # stay on free tier
                }
            )

            if response.status_code != 200:
                return []

            # Parse the HTML with BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")
            posts = _parse_posts(soup, max_posts)
            return posts

    except Exception as e:
        # Never crash enrichment — just return empty
        print(f"LinkedIn scrape failed for {linkedin_url}: {e}")
        return []


def _parse_posts(soup: BeautifulSoup, max_posts: int) -> list[dict]:
    """
    Extract post text from LinkedIn HTML.
    LinkedIn's HTML structure changes — we try multiple selectors.
    """
    posts = []

    # LinkedIn uses these CSS classes for post content
    # (These may need updating if LinkedIn changes their HTML)
    selectors = [
        "span.break-words",
        "div.feed-shared-update-v2__description",
        "div.update-components-text",
    ]

    post_elements = []
    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            post_elements = elements
            break

    for element in post_elements[:max_posts]:
        text = element.get_text(separator=" ", strip=True)

        # Skip very short posts (likely artifacts, not real content)
        if len(text) < 50:
            continue

        # Clean up LinkedIn's formatting artifacts
        text = re.sub(r'\s+', ' ', text)        # collapse whitespace
        text = re.sub(r'…see more$', '', text)  # remove "...see more" truncation

        posts.append({
            "text": text.strip(),
            "date": date.today(),    # LinkedIn doesn't expose exact date in HTML easily
            "likes": 0,              # engagement data not reliably scrapable on free tier
            "comments": 0,
        })

    return posts


async def fetch_company_jobs(company_website: str) -> list[str]:
    """
    Scrape company job postings to detect if they're hiring SDRs/BDRs.
    Returns list of job titles found.
    """
    if not company_website or not SCRAPERAPI_KEY:
        return []

    # Try common job page URLs
    job_urls = [
        f"{company_website}/careers",
        f"{company_website}/jobs",
    ]

    for url in job_urls:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(
                    SCRAPERAPI_URL,
                    params={"api_key": SCRAPERAPI_KEY, "url": url}
                )

                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                text = soup.get_text(separator=" ").lower()

                # Extract job titles that suggest sales hiring
                sales_roles = []
                role_keywords = ["sdr", "bdr", "account executive", "sales development",
                                 "business development", "ae ", "account manager"]

                for keyword in role_keywords:
                    if keyword in text:
                        sales_roles.append(keyword.upper().strip())

                if sales_roles:
                    return list(set(sales_roles))

        except Exception:
            continue

    return []