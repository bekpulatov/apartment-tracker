import re
import json
from playwright.sync_api import sync_playwright
from config import ROOMS_MIN

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Uluwatu has no separate apartment/house category on this site — villas are the market.
SEARCH_PAGE_URL = "https://bali-home-immo.com/realestate-property/for-rent/villa/monthly/uluwatu"

# Approximate IDR → USD rate, used since the site only lists prices in IDR
IDR_TO_USD = 1 / 17700

BEDROOM_RE = re.compile(r"(\d+)\s*bedroom", re.IGNORECASE)


def _get_inertia_version(page) -> str:
    # This is a Laravel Inertia.js app: the same JSON payload that hydrates the page
    # is available directly by replaying the request with these headers, no HTML parsing needed.
    data_page = page.evaluate("document.querySelector('#app').getAttribute('data-page')")
    return json.loads(data_page)["version"]


def _fetch_page_json(page, version: str, url: str) -> dict:
    result = page.evaluate(
        """async ({url, version}) => {
            const r = await fetch(url, {
                headers: { "X-Inertia": "true", "X-Inertia-Version": version, Accept: "text/html, application/xhtml+xml" }
            });
            return { status: r.status, text: await r.text() };
        }""",
        {"url": url, "version": version},
    )
    if result["status"] != 200:
        raise RuntimeError(f"HTTP {result['status']} from Bali Home Immo")
    return json.loads(result["text"])


def fetch_listings(max_pages: int = 3) -> list[dict]:
    listings = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                context = browser.new_context(user_agent=USER_AGENT, locale="en-US")
                page = context.new_page()
                page.goto(SEARCH_PAGE_URL, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(1500)
                version = _get_inertia_version(page)

                url = SEARCH_PAGE_URL
                for _ in range(max_pages):
                    if not url:
                        break
                    data = _fetch_page_json(page, version, url)
                    props = data.get("props", {})
                    properties = props.get("properties", [])
                    if not properties:
                        break

                    for prop in properties:
                        monthly = prop.get("prices", {}).get("monthly")
                        if monthly is None:
                            continue
                        price_usd = float(monthly) * IDR_TO_USD

                        name = prop.get("name", "")
                        m = BEDROOM_RE.search(name)
                        # No bedroom count in the title is rare on this site; when it happens, let it through
                        if m and int(m.group(1)) < ROOMS_MIN:
                            continue

                        info_box = prop.get("info_box_by_category", {}).get("monthly", [])
                        furnished = None
                        for item in info_box:
                            if item.get("name") == "Furniture":
                                furnished = item.get("value", "").lower() == "furnished"

                        images = prop.get("images") or []
                        lat = prop.get("latitude")
                        lon = prop.get("longitude")
                        address = ", ".join(x for x in [prop.get("area"), prop.get("subarea")] if x)

                        listings.append({
                            "id": f"bali_{prop['id']}",
                            "source": "Bali Home Immo",
                            "title": name,
                            "price": f"${price_usd:,.0f}/mo (IDR {float(monthly):,.0f})",
                            "price_usd": price_usd,
                            "url": prop.get("detail_urls", {}).get("monthly") or SEARCH_PAGE_URL,
                            "image_url": images[0] if images else None,
                            "address": address or "Uluwatu, Bali",
                            "description": name,
                            "furnished": furnished,
                            # These are agency listings, not daily classifieds — they stay live for
                            # months, so "recently posted" isn't meaningful. Leaving posted_at unset
                            # means the recency filter passes everything through; the seen-listings
                            # database is what stops repeat notifications.
                            "posted_at": None,
                            "lat": float(lat) if lat else None,
                            "lon": float(lon) if lon else None,
                            # No walkable-radius concept here — the search is already scoped to Uluwatu.
                            "market": "bali_uluwatu",
                        })

                    url = props.get("pagination", {}).get("next_page_url")
            finally:
                browser.close()

    except Exception as e:
        print(f"[BaliHomeImmo] Error: {e}")

    return listings
