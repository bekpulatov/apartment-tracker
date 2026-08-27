import os
from dotenv import load_dotenv

load_dotenv()

RADIUS_KM = 3.0

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HOME_LAT = os.getenv("HOME_LAT")
HOME_LON = os.getenv("HOME_LON")

CHECK_INTERVAL_MINUTES = 30
DB_PATH = "listings.db"

# Price filter (USD/month)
PRICE_MIN_USD = 300
PRICE_MAX_USD = 1500

# Listing filters
# OLX doesn't track a "furnished" attribute for commercial/office premises at all,
# so this must stay off while the tracker is searching offices, not apartments.
REQUIRE_FURNISHED = False
REQUIRE_PHOTO = True
MAX_LISTING_AGE_DAYS = 1

# Unused while searching offices (a whole office unit IS the workspace) — kept
# for the dormant apartment/villa scrapers, which still import this.
ROOMS_MIN = 2
