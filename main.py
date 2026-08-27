import time
import schedule
from db import init_db, is_seen, mark_seen
from location import is_within_radius, distance_km, walk_minutes
from notifier import notify
from filters import passes_all
from scrapers import olx_office
from config import CHECK_INTERVAL_MINUTES


def check():
    print(f"[Tracker] Checking for new listings...")
    all_listings = olx_office.fetch_listings()
    new_count = 0

    for listing in all_listings:
        if is_seen(listing["id"]):
            continue

        ok, reason = passes_all(listing)
        if not ok:
            print(f"  [skip] {reason}: {listing['title']}")
            mark_seen(listing)
            continue

        if not is_within_radius(listing["lat"], listing["lon"]):
            print(f"  [skip] Too far: {listing['title']}")
            mark_seen(listing)
            continue
        listing["walk_minutes"] = walk_minutes(distance_km(listing["lat"], listing["lon"]))

        print(f"  [NEW] {listing['title']} — {listing['price']}")
        # Mark seen before notifying: if the run gets interrupted mid-notify, we'd
        # rather silently miss one listing than spam a duplicate on the next run.
        mark_seen(listing)
        notify(listing)
        new_count += 1

    print(f"[Tracker] Done. {new_count} new listing(s) sent.")


def main():
    init_db()
    print(f"[Tracker] Starting. Checking every {CHECK_INTERVAL_MINUTES} minutes.")
    check()  # run immediately on start
    schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(check)
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
