import re
import json
from datetime import datetime, timezone
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

# Long-term apartment rentals in Tashkent
BASE_URL = "https://www.olx.uz/nedvizhimost/kvartiry/arenda-dolgosrochnaya/"


def _parse_date(iso_str: str) -> datetime | None:
    if not iso_str:
        return None
    try:
        return datetime.fromisoformat(iso_str).astimezone(timezone.utc)
    except Exception:
        return None


def _get_param(params: list, key: str) -> str | None:
    for p in params:
        if p.get("key") == key:
            return p.get("normalizedValue")
    return None


def _fetch_page(page: int) -> list:
    url = BASE_URL if page == 0 else f"{BASE_URL}?page={page}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    match = re.search(r'window\.__PRERENDERED_STATE__= "(.+?)";', r.text)
    if not match:
        return []
    json_str = json.loads('"' + match.group(1) + '"')
    data = json.loads(json_str)
    return data["listing"]["listing"]["ads"]


def fetch_listings(max_pages: int = 1) -> list[dict]:
    listings = []
    seen_ids = set()
    try:
        for page in range(max_pages):
            ads = _fetch_page(page)
            if not ads:
                break

            for ad in ads:
                if ad["id"] in seen_ids:
                    continue
                seen_ids.add(ad["id"])
                location = ad.get("location", {})
                if location.get("cityNormalizedName") != "tashkent":
                    continue

                params = ad.get("params", [])

                rooms = _get_param(params, "number_of_rooms")
                if rooms and rooms.strip() != "1":
                    continue

                price_data = ad.get("price", {}).get("regularPrice")
                if price_data:
                    price_uzs = price_data.get("value", 0)
                    price_str = f"{price_uzs:,} UZS"
                else:
                    price_str = "Price not listed"

                photos = ad.get("photos", [])
                image_url = photos[0] if photos else None

                furnished_val = _get_param(params, "furnished")
                description = ad.get("description", "")
                if furnished_val == "yes":
                    description = "furnished " + description

                listings.append({
                    "id": f"olx_{ad['id']}",
                    "source": "OLX.uz",
                    "title": ad.get("title", ""),
                    "price": price_str,
                    "url": ad.get("url", ""),
                    "image_url": image_url,
                    "address": location.get("pathName", "Tashkent"),
                    "description": description,
                    "posted_at": _parse_date(ad.get("lastRefreshTime") or ad.get("createdTime")),
                    "lat": ad.get("map", {}).get("lat"),
                    "lon": ad.get("map", {}).get("lon"),
                })

    except Exception as e:
        print(f"[OLX] Error: {e}")

    return listings
