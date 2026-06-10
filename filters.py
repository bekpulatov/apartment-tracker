import re
from datetime import datetime, timedelta, timezone
from config import PRICE_MIN_USD, PRICE_MAX_USD, REQUIRE_FURNISHED, REQUIRE_PHOTO, MAX_LISTING_AGE_DAYS

# Approximate UZS → USD rate, used only when the source gives no USD price
UZS_TO_USD = 1 / 12700


def parse_price_usd(price_str: str) -> float | None:
    if not price_str:
        return None
    price_str = price_str.replace(" ", "").replace("\xa0", "")

    numbers = re.findall(r"[\d]+", price_str.replace(",", ""))
    if not numbers:
        return None
    amount = float("".join(numbers[:2]) if len(numbers) > 1 and len(numbers[0]) <= 3 else numbers[0])

    lower = price_str.lower()
    if "$" in price_str or "usd" in lower:
        return amount
    if "сум" in lower or "uzs" in lower or "so'm" in lower or "sum" in lower:
        return amount * UZS_TO_USD
    return amount if amount < 10000 else amount * UZS_TO_USD


def passes_price(listing: dict) -> bool:
    price = listing.get("price_usd")
    if price is None:
        price = parse_price_usd(listing.get("price", ""))
    if price is None:
        return True  # can't determine, include it
    return PRICE_MIN_USD <= price <= PRICE_MAX_USD


def passes_furnished(listing: dict) -> bool:
    if not REQUIRE_FURNISHED:
        return True
    # Prefer the structured field from the source; fall back to keywords
    if listing.get("furnished") is not None:
        return listing["furnished"]
    text = (listing.get("title", "") + " " + listing.get("description", "")).lower()
    keywords = ["меблир", "furnished", "mebel", "мебел"]
    return any(k in text for k in keywords)


def passes_photo(listing: dict) -> bool:
    if not REQUIRE_PHOTO:
        return True
    return bool(listing.get("image_url"))


def passes_recency(listing: dict) -> bool:
    posted_at = listing.get("posted_at")
    if not posted_at:
        return True  # can't determine, include it
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_LISTING_AGE_DAYS)
    return posted_at >= cutoff


def passes_all(listing: dict) -> tuple[bool, str]:
    if not passes_photo(listing):
        return False, "no photo"
    if not passes_price(listing):
        price = listing.get("price_usd") or parse_price_usd(listing.get("price", ""))
        return False, f"price ${price:.0f} out of range" if price else "price unknown"
    if not passes_furnished(listing):
        return False, "not furnished"
    if not passes_recency(listing):
        return False, "listing too old"
    return True, "ok"
