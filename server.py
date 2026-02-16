import os
import logging
from urllib.parse import urlencode
from urllib.robotparser import RobotFileParser
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastmcp import FastMCP

VERSION = "0.2.0"
IGNORE_ROBOTS_TXT = os.environ.get("IGNORE_ROBOTS_TXT", "false").lower() == "true"
PORT = int(os.environ.get("PORT", "8080"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("airbnb-mcp")

robots_txt_content: Optional[str] = None

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ClaudeBot/1.0; +https://www.anthropic.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


async def fetch_robots_txt():
    global robots_txt_content
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://www.airbnb.com/robots.txt")
            robots_txt_content = response.text
            logger.info("Successfully fetched robots.txt")
    except Exception as e:
        logger.error(f"Failed to fetch robots.txt: {e}")


def is_allowed_by_robots(path: str) -> bool:
    if IGNORE_ROBOTS_TXT or not robots_txt_content:
        return True
    rp = RobotFileParser()
    rp.parse(robots_txt_content.splitlines())
    return rp.can_fetch("ClaudeBot", f"https://www.airbnb.com{path}")


async def ensure_robots():
    if robots_txt_content is None and not IGNORE_ROBOTS_TXT:
        await fetch_robots_txt()


# ===== FastAPI app with tool endpoints =====

base_app = FastAPI(title="Airbnb MCP Server")


@base_app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "version": VERSION}


@base_app.post("/airbnb/search")
async def airbnb_search(
    location: str,
    checkin: Optional[str] = None,
    checkout: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    pets: int = 0,
):
    """Search Airbnb listings by location, dates, and filters"""
    await ensure_robots()

    params = {"query": location}
    if checkin:
        params["checkin"] = checkin
    if checkout:
        params["checkout"] = checkout
    if adults:
        params["adults"] = str(adults)
    if children:
        params["children"] = str(children)
    if infants:
        params["infants"] = str(infants)
    if pets:
        params["pets"] = str(pets)

    search_url = f"https://www.airbnb.com/s/homes?{urlencode(params)}"

    if not is_allowed_by_robots("/s/homes"):
        return {"error": "Access not allowed by robots.txt"}

    logger.info(f"Fetching Airbnb search: {search_url}")

    async with httpx.AsyncClient() as client:
        response = await client.get(search_url, headers=HEADERS, follow_redirects=True, timeout=30.0)

    if response.status_code != 200:
        return {"error": f"Failed to fetch: {response.status_code}"}

    soup = BeautifulSoup(response.text, "html.parser")
    listings = []

    for element in soup.select('[itemprop="itemListElement"]'):
        title_el = element.select_one('[data-testid="listing-card-title"]')
        price_el = element.select_one('[data-testid="listing-card-price"]')
        rating_el = element.select_one('[aria-label*="rating"]')
        url_el = element.select_one('a[href^="/rooms/"]')
        img_el = element.select_one("img")

        title = title_el.get_text(strip=True) if title_el else None
        url = url_el.get("href") if url_el else None

        if title and url:
            if not url.startswith("http"):
                url = f"https://www.airbnb.com{url}"
            listings.append({
                "title": title,
                "price": price_el.get_text(strip=True) if price_el else None,
                "rating": rating_el.get("aria-label") if rating_el else None,
                "url": url,
                "image": img_el.get("src") if img_el else None,
            })

    logger.info(f"Search completed: {len(listings)} results")
    return {"listings": listings, "search_params": {"location": location}}


@base_app.post("/airbnb/listing")
async def airbnb_listing_details(listing_id: str):
    """Get detailed information about a specific Airbnb listing"""
    await ensure_robots()

    listing_url = f"https://www.airbnb.com/rooms/{listing_id}"

    if not is_allowed_by_robots(f"/rooms/{listing_id}"):
        return {"error": "Access not allowed by robots.txt"}

    logger.info(f"Fetching listing details: {listing_id}")

    async with httpx.AsyncClient() as client:
        response = await client.get(listing_url, headers=HEADERS, follow_redirects=True, timeout=30.0)

    if response.status_code != 200:
        return {"error": f"Failed to fetch: {response.status_code}"}

    soup = BeautifulSoup(response.text, "html.parser")

    h1 = soup.find("h1")
    desc_section = soup.select_one('[data-section-id="DESCRIPTION_DEFAULT"] span')
    amenities_els = soup.select(
        '[data-section-id="AMENITIES_DEFAULT"] [data-testid="modal-container"] div'
    )
    host_section = soup.select_one('[data-section-id="HOST_PROFILE_DEFAULT"] h2')

    reviews = []
    for review_el in soup.select("[data-review-id]"):
        text_el = review_el.select_one('[data-testid="review-text"]')
        rating_el = review_el.select_one('[aria-label*="rating"]')
        author_el = review_el.select_one('[data-testid="review-author"]')
        reviews.append({
            "text": text_el.get_text(strip=True) if text_el else "",
            "rating": rating_el.get("aria-label") if rating_el else None,
            "author": author_el.get_text(strip=True) if author_el else "",
        })

    details = {
        "title": h1.get_text(strip=True) if h1 else "",
        "description": desc_section.get_text(strip=True) if desc_section else "",
        "amenities": [el.get_text(strip=True) for el in amenities_els],
        "host": host_section.get_text(strip=True) if host_section else "",
        "reviews": reviews,
    }

    logger.info(f"Listing details fetched: {listing_id}")
    return details


# ===== FastMCP integration =====

mcp = FastMCP.from_fastapi(app=base_app, name="Airbnb MCP Server")
mcp_app = mcp.http_app(path="/mcp")


app = FastAPI(
    routes=[*mcp_app.routes, *base_app.routes],
    lifespan=mcp_app.lifespan,
)

if __name__ == "__main__":
    import uvicorn

    logger.info(f"Airbnb MCP Server starting on port {PORT} (FastMCP mode, v{VERSION})")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
