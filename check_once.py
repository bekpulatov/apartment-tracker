"""Single-run check used by GitHub Actions (runs once and exits)."""
from db import init_db, is_seen, mark_seen
from location import is_within_radius, distance_km, walk_minutes
from notifier import notify
from filters import passes_all
from scrapers import olx_office

def main():
    init_db()
    listings = olx_office.fetch_listings()
    new_count = 0

    for listing in listings:
        if is_seen(listing["id"]):
            continue

        ok, reason = passes_all(listing)
        if not ok:
            print(f"  [skip] {reason}: {listing['title']}")
            mark_seen(listing)
            continue

        if not is_within_radius(listing["lat"], listing["lon"]):
            print(f"  [skip] too far: {listing['title']}")
            mark_seen(listing)
            continue
        listing["walk_minutes"] = walk_minutes(distance_km(listing["lat"], listing["lon"]))

        print(f"  [NEW] {listing['title']} — {listing['price']}")
        # Mark seen before notifying: if the run gets interrupted mid-notify, we'd
        # rather silently miss one listing than spam a duplicate on the next run.
        mark_seen(listing)
        notify(listing)
        new_count += 1

    print(f"Done. {new_count} new listing(s) sent.")

if __name__ == "__main__":
    main()
