# Uybor.uz loads listings via client-side JavaScript — cannot be scraped
# without a headless browser. Disabled for now.

def fetch_listings() -> list[dict]:
    print("[Uybor] Skipped (client-side rendered, requires headless browser)")
    return []
