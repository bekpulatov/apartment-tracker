from datetime import datetime, timezone
import json
from playwright.sync_api import sync_playwright

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# OLX puts a bot-detection challenge in front of the raw API — loading the search
# page first in a real browser session gets us past it before we call the API.
SEARCH_PAGE_URL = "https://www.olx.uz/nedvizhimost/kommercheskie-pomeshcheniya/arenda/tashkent/"
API_URL = "https://www.olx.uz/api/v1/offers/"
# Category 11 = commercial premises for rent — mixes offices, shops, warehouses, restaurants,
# etc. together. There's no separate "offices only" category, so premise_type filters it down.
CATEGORY_ID = 11
CITY_ID = 4
PAGE_SIZE = 40
# premise_type key meaning "Офисы" (Offices), confirmed against ~200 live listings
OFFICE_PREMISE_TYPE_KEY = "4"


def _parse_date(iso_str: str) -> datetime | None:
    if not iso_str:
        return None
    try:
        return datetime.fromisoformat(iso_str).astimezone(timezone.utc)
    except Exception:
        return None


def _get_param(ad: dict, key: str):
    for p in ad.get("params", []):
        if p.get("key") == key:
            return p.get("value")
    return None


def _extract_price(ad: dict) -> tuple[float | None, str]:
    """Returns (price_usd, display_string). OLX stores prices in UYE (= USD)."""
    value = _get_param(ad, "price")
    if not value:
        return None, "Price not listed"
    amount = value.get("value")
    currency = value.get("currency", "")
    label = value.get("label") or f"{amount} {currency}"
    if amount is None:
        return None, label
    if currency in ("UYE", "USD"):
        return float(amount), f"${amount:.0f} ({label})"
    if currency == "UZS":
        return float(amount) / 12700, label
    return None, label


def _fetch_page_json(page, offset: int) -> dict:
    url = f"{API_URL}?offset={offset}&limit={PAGE_SIZE}&category_id={CATEGORY_ID}&city_id={CITY_ID}"
    result = page.evaluate(
        """async (url) => {
            const r = await fetch(url, { headers: { Accept: "application/json" } });
            return { status: r.status, text: await r.text() };
        }""",
        url,
    )
    if result["status"] != 200:
        raise RuntimeError(f"HTTP {result['status']} from OLX API")
    return json.loads(result["text"])


def fetch_listings(max_pages: int = 3) -> list[dict]:
    listings = []
    seen_ids = set()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                context = browser.new_context(user_agent=USER_AGENT, locale="ru-RU")
                page = context.new_page()
                page.goto(SEARCH_PAGE_URL, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)

                for page_num in range(max_pages):
                    data = _fetch_page_json(page, page_num * PAGE_SIZE)
                    ads = data.get("data", [])
                    if not ads:
                        break

                    for ad in ads:
                        if ad["id"] in seen_ids:
                            continue
                        seen_ids.add(ad["id"])

                        if ad.get("location", {}).get("city", {}).get("id") != CITY_ID:
                            continue

                        premise_type = _get_param(ad, "premise_type")
                        premise_keys = premise_type.get("key") if isinstance(premise_type, dict) else None
                        if not premise_keys or OFFICE_PREMISE_TYPE_KEY not in premise_keys:
                            continue

                        price_usd, price_str = _extract_price(ad)

                        photos = ad.get("photos", [])
                        image_url = None
                        if photos:
                            image_url = photos[0].get("link", "").replace("{width}", "800").replace("{height}", "600")

                        loc = ad.get("location", {})
                        district = loc.get("district", {}).get("name", "")
                        address = ", ".join(x for x in [loc.get("city", {}).get("name", ""), district] if x)

                        listings.append({
                            "id": f"olxoffice_{ad['id']}",
                            "source": "OLX.uz",
                            "title": ad.get("title", ""),
                            "price": price_str,
                            "price_usd": price_usd,
                            "url": ad.get("url", ""),
                            "image_url": image_url,
                            "address": address or "Tashkent",
                            "description": ad.get("description", ""),
                            "furnished": None,  # not a field OLX tracks for commercial premises
                            # created_time = when the listing was actually posted.
                            # Never use last_refresh_time: paying for promotion bumps it.
                            "posted_at": _parse_date(ad.get("created_time")),
                            "lat": ad.get("map", {}).get("lat"),
                            "lon": ad.get("map", {}).get("lon"),
                        })
            finally:
                browser.close()

    except Exception as e:
        print(f"[OLXOffice] Error: {e}")

    return listings
