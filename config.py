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
REQUIRE_FURNISHED = True
REQUIRE_PHOTO = True
MAX_LISTING_AGE_DAYS = 1

# Need at least a bedroom + a separate room to work from
ROOMS_MIN = 2
