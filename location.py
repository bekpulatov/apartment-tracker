from geopy.distance import geodesic
from config import RADIUS_KM

# Taras Shevchenko 40, Tashkent
HOME_COORDS = (41.2962964, 69.2812385)


def is_within_radius(lat: float, lon: float) -> bool:
    if lat is None or lon is None:
        return True  # include listing if coordinates unknown
    distance_km = geodesic(HOME_COORDS, (lat, lon)).km
    return distance_km <= RADIUS_KM
