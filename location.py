from geopy.distance import geodesic
from config import RADIUS_KM, HOME_LAT, HOME_LON

if not HOME_LAT or not HOME_LON:
    raise RuntimeError("HOME_LAT and HOME_LON must be set (see .env.example)")
HOME_COORDS = (float(HOME_LAT), float(HOME_LON))

WALK_SPEED_KMH = 4.5


def distance_km(lat: float, lon: float) -> float | None:
    if lat is None or lon is None:
        return None
    return geodesic(HOME_COORDS, (lat, lon)).km


def walk_minutes(km: float | None) -> int | None:
    if km is None:
        return None
    return round(km / WALK_SPEED_KMH * 60)


def is_within_radius(lat: float, lon: float) -> bool:
    # Strict: if a listing has no coordinates we can't verify it's nearby, so skip it
    km = distance_km(lat, lon)
    if km is None:
        return False
    return km <= RADIUS_KM
