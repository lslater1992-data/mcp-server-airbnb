import os
import re
import json
import logging
from urllib.parse import urlencode, quote
from urllib.robotparser import RobotFileParser
from typing import Optional, List

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastmcp import FastMCP
from starlette.responses import JSONResponse


VERSION = "0.2.0"
IGNORE_ROBOTS_TXT = os.environ.get("IGNORE_ROBOTS_TXT", "false").lower() == "true"
PORT = int(os.environ.get("PORT", "8080"))
BEARER_TOKEN = os.environ.get("LEX_BEARER_TOKEN", "test-token-123")
AUTH_ENABLED = os.environ.get("LEX_ENABLE_AUTH", "false").lower() == "true"
SCRAPEOPS_API_KEY = os.environ.get("SCRAPEOPS_API_KEY")


def get_scrapeops_url(target_url: str) -> str:
    """Route through ScrapeOps proxy if API key is configured."""
    if SCRAPEOPS_API_KEY:
        return f"https://proxy.scrapeops.io/v1/?api_key={SCRAPEOPS_API_KEY}&url={quote(target_url)}&render_js=0&residential=1"
    return target_url

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("airbnb-mcp")

robots_txt_content: Optional[str] = None

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


async def fetch_robots_txt():
    global robots_txt_content
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://www.airbnb.com/robots.txt", headers=HEADERS)
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


def parse_listings_from_json(html: str) -> List[dict]:
    """Extract listings from embedded JSON in Airbnb's HTML."""
    data = None

    # Strategy 1: BeautifulSoup — <script id="data-deferred-state-0">
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", {"id": "data-deferred-state-0"})
    if not script:
        # Strategy 2: Any script tag with "searchResults" or "staysSearch"
        for s in soup.find_all("script"):
            text = s.string or ""
            if "searchResults" in text or "staysSearch" in text:
                script = s
                break

    if script and script.string:
        try:
            data = json.loads(script.string)
            logger.info(f"Parsed JSON from script tag: {len(script.string)} chars")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")

    # Strategy 3: Regex fallback if BeautifulSoup missed it
    if data is None:
        script_match = re.search(r'<script[^>]*id="data-deferred-state-0"[^>]*>(.*?)</script>', html, re.DOTALL)
        if script_match:
            try:
                data = json.loads(script_match.group(1))
                logger.info(f"Parsed JSON via regex fallback: {len(script_match.group(1))} chars")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse regex-extracted JSON: {e}")

    if data is None:
        logger.warning(f"No JSON data found in HTML ({len(html)} total chars)")
        return []

    # Navigate to searchResults via known paths
    search_results = None
    for niobe_key in ["niobeClientData", "niobeMinimalClientData"]:
        niobe = data.get(niobe_key, []) if isinstance(data, dict) else []
        if niobe and isinstance(niobe[0], list) and len(niobe[0]) >= 2:
            search_results = (niobe[0][1]
                .get("data", {})
                .get("presentation", {})
                .get("staysSearch", {})
                .get("results", {})
                .get("searchResults", []))
            if search_results:
                logger.info(f"Found {len(search_results)} results via {niobe_key}")
                break

    if not search_results:
        logger.warning("Could not find searchResults in JSON data")
        return []

    listings = []
    for result in search_results:
        try:
            listing = {
                "title": result.get("title", ""),
                "listing_id": result.get("propertyId", ""),
                "rating": result.get("avgRatingLocalized", ""),
                "url": f"https://www.airbnb.com/rooms/{result.get('propertyId', '')}",
                "image": None,
                "price": None,
                "subtitle": result.get("subtitle", ""),
            }

            # Extract price from structuredDisplayPrice
            price_data = result.get("structuredDisplayPrice", {})
            if price_data:
                primary = price_data.get("primaryLine", {})
                listing["price"] = primary.get("accessibilityLabel") or primary.get("price", "")

            # Extract first image
            pics = result.get("contextualPictures", [])
            if pics:
                listing["image"] = pics[0].get("picture", "")

            listings.append(listing)
        except Exception as e:
            logger.warning(f"Failed to parse listing result: {e}")
            continue

    return listings


@base_app.post("/search")
async def search_listings(
    location: str,
    checkin: Optional[str] = None,
    checkout: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    pets: int = 0,
    max_pages: int = 1,
):
    """Search Airbnb listings by location, dates, and filters. Use max_pages to fetch more results (each page has ~18 listings). Stops automatically when no more results are found."""
    await ensure_robots()

    if max_pages < 1:
        max_pages = 1

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

    if not is_allowed_by_robots("/s/homes"):
        return {"error": "Access not allowed by robots.txt"}

    all_listings = []

    async with httpx.AsyncClient() as client:
        for page in range(max_pages):
            page_params = {**params}
            if page > 0:
                page_params["items_offset"] = str(page * 18)

            search_url = f"https://www.airbnb.com/s/homes?{urlencode(page_params)}"
            logger.info(f"Fetching Airbnb search page {page + 1}: {search_url}")

            fetch_url = get_scrapeops_url(search_url)
            response = await client.get(fetch_url, headers=HEADERS, follow_redirects=True, timeout=60.0)

            if response.status_code != 200:
                logger.warning(f"Page {page + 1} fetch failed: {response.status_code}")
                break

            page_listings = parse_listings_from_json(response.text)

            if not page_listings:
                logger.warning(f"No listings found on page {page + 1}. HTML preview (first 5000 chars): {response.text[:5000]}")
                break

            all_listings.extend(page_listings)
            logger.info(f"Page {page + 1}: {len(page_listings)} listings found")

    logger.info(f"Search completed: {len(all_listings)} total results across {min(page + 1, max_pages)} pages")
    return {
        "listings": all_listings,
        "total_results": len(all_listings),
        "search_params": {"location": location, "pages_fetched": min(page + 1, max_pages)},
    }


@base_app.post("/listing")
async def get_listing(listing_id: str):
    """Get detailed information about a specific Airbnb listing"""
    await ensure_robots()

    listing_url = f"https://www.airbnb.com/rooms/{listing_id}"

    if not is_allowed_by_robots(f"/rooms/{listing_id}"):
        return {"error": "Access not allowed by robots.txt"}

    logger.info(f"Fetching listing details: {listing_id}")

    fetch_url = get_scrapeops_url(listing_url)

    async with httpx.AsyncClient() as client:
        response = await client.get(fetch_url, headers=HEADERS, follow_redirects=True, timeout=60.0)

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

os.environ["FASTMCP_EXPERIMENTAL_ENABLE_NEW_OPENAPI_PARSER"] = "true"
mcp = FastMCP.from_fastapi(app=base_app, name="Airbnb MCP Server")
mcp_app = mcp.http_app(path="/mcp")

app = FastAPI(
    routes=[*mcp_app.routes, *base_app.routes],
    lifespan=mcp_app.lifespan,
)

if AUTH_ENABLED and BEARER_TOKEN:
    @app.middleware("http")
    async def auth_middleware(request, call_next):
        if request.url.path == "/health":
            return await call_next(request)
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer ") or auth_header[7:] != BEARER_TOKEN:
            return JSONResponse(status_code=401, content={"error": "Unauthorized"})
        return await call_next(request)


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Airbnb MCP Server starting on port {PORT} (FastMCP mode, v{VERSION})")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
