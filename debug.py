from scrapers import olx
from filters import passes_all
from location import is_within_radius

listings = olx.fetch_listings()
print(f"OLX: {len(listings)} listings fetched (1-room, Tashkent)\n")

for l in listings:
    ok, reason = passes_all(l)
    in_range = is_within_radius(l["lat"], l["lon"])
    status = "MATCH" if ok and in_range else f"skip ({reason if not ok else 'too far'})"
    print(f"  [{status}] {l['title']} | {l['price']} | {l['address'][:40]}")
