from datetime import datetime, timezone
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

# OLX JSON API — category 1147 = long-term apartment rentals, city 4 = Tashkent
API_URL = "https://www.olx.uz/api/v1/offers/"
CATEGORY_ID = 1147
CITY_ID = 4
PAGE_SIZE = 40


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


def fetch_listings(max_pages: int = 3) -> list[dict]:
    listings = []
    seen_ids = set()
    try:
        for page in range(max_pages):
            r = requests.get(API_URL, headers=HEADERS, timeout=15, params={
                "offset": page * PAGE_SIZE,
                "limit": PAGE_SIZE,
                "category_id": CATEGORY_ID,
                "city_id": CITY_ID,
            })
            ads = r.json().get("data", [])
            if not ads:
                break

            for ad in ads:
                if ad["id"] in seen_ids:
                    continue
                seen_ids.add(ad["id"])

                if ad.get("location", {}).get("city", {}).get("id") != CITY_ID:
                    continue

                rooms = _get_param(ad, "number_of_rooms")
                rooms_key = rooms.get("key") if isinstance(rooms, dict) else rooms
                if rooms_key and str(rooms_key).strip() != "1":
                    continue

                price_usd, price_str = _extract_price(ad)

                photos = ad.get("photos", [])
                image_url = None
                if photos:
                    image_url = photos[0].get("link", "").replace("{width}", "800").replace("{height}", "600")

                furnished_val = _get_param(ad, "furnished")
                furnished_key = furnished_val.get("key") if isinstance(furnished_val, dict) else furnished_val

                loc = ad.get("location", {})
                district = loc.get("district", {}).get("name", "")
                address = ", ".join(x for x in [loc.get("city", {}).get("name", ""), district] if x)

                listings.append({
                    "id": f"olx_{ad['id']}",
                    "source": "OLX.uz",
                    "title": ad.get("title", ""),
                    "price": price_str,
                    "price_usd": price_usd,
                    "url": ad.get("url", ""),
                    "image_url": image_url,
                    "address": address or "Tashkent",
                    "description": ad.get("description", ""),
                    "furnished": furnished_key == "yes" if furnished_key is not None else None,
                    # created_time = when the listing was actually posted.
                    # Never use last_refresh_time: paying for promotion bumps it.
                    "posted_at": _parse_date(ad.get("created_time")),
                    "lat": ad.get("map", {}).get("lat"),
                    "lon": ad.get("map", {}).get("lon"),
                })

    except Exception as e:
        print(f"[OLX] Error: {e}")

    return listings
