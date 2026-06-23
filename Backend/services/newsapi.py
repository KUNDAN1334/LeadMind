# backend/services/newsapi.py
# Fetches recent company news — funding rounds, acquisitions, launches
# Free tier: 100 requests/day

import httpx
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/everything"


async def fetch_company_news(company_name: str, days_back: int = 90) -> list[dict]:
    """
    Fetch recent news mentions for a company.

    Returns list of:
    {
        "title": "...",
        "description": "...",
        "published_at": "2024-01-15",
        "source": "TechCrunch",
        "url": "https://..."
    }
    """

    if not company_name or not NEWS_API_KEY:
        return []

    # Only look at news from the last N days
    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                NEWS_API_URL,
                params={
                    "q": f'"{company_name}"',   # exact phrase match
                    "from": from_date,
                    "sortBy": "relevancy",
                    "language": "en",
                    "pageSize": 10,             # max 10 articles
                    "apiKey": NEWS_API_KEY,
                }
            )

            if response.status_code != 200:
                return []

            data = response.json()
            articles = data.get("articles", [])

            # Normalize to our format
            return [
                {
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "published_at": article.get("publishedAt", "")[:10],
                    "source": article.get("source", {}).get("name", ""),
                    "url": article.get("url", ""),
                }
                for article in articles
                if article.get("title")   # skip articles with no title
            ]

    except Exception as e:
        print(f"NewsAPI failed for {company_name}: {e}")
        return []