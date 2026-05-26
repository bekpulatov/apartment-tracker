import time
import schedule
from db import init_db, is_seen, mark_seen
from location import is_within_radius
from notifier import notify
from filters import passes_all
from scrapers import olx, uybor
from config import CHECK_INTERVAL_MINUTES


def check():
    print(f"[Tracker] Checking for new listings...")
    all_listings = olx.fetch_listings() + uybor.fetch_listings()
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

        print(f"  [NEW] {listing['title']} — {listing['price']}")
        notify(listing)
        mark_seen(listing)
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
