"""Core freight rate & ETA estimation logic — pure functions, no Flask,
so they're easy to unit test in isolation.
"""
import math
from datetime import date, timedelta

# lat, lon for supported cities (kept small & deliberate rather than
# pulling in a geocoding dependency this sandbox can't install).
CITY_COORDS = {
    "atlanta, ga": (33.7490, -84.3880),
    "charlotte, nc": (35.2271, -80.8431),
    "chicago, il": (41.8781, -87.6298),
    "columbus, oh": (39.9612, -82.9988),
    "dallas, tx": (32.7767, -96.7970),
    "denver, co": (39.7392, -104.9903),
    "houston, tx": (29.7604, -95.3698),
    "lake mary, fl": (28.7589, -81.3226),
    "long beach, ca": (33.7701, -118.1937),
    "los angeles, ca": (34.0522, -118.2437),
    "memphis, tn": (35.1495, -90.0490),
    "miami, fl": (25.7617, -80.1918),
    "newark, nj": (40.7357, -74.1724),
    "norfolk, va": (36.8508, -76.2859),
    "orlando, fl": (28.5383, -81.3792),
    "savannah, ga": (32.0809, -81.0912),
    "seattle, wa": (47.6062, -122.3321),
}

# per-mile rate, average mph, and flat fuel surcharge per mode
MODE_PROFILE = {
    "Truck":  {"per_mile": 2.10, "mph": 47,  "surcharge": 45.00},
    "Rail":   {"per_mile": 0.95, "mph": 30,  "surcharge": 60.00},
    "Ocean":  {"per_mile": 0.35, "mph": 18,  "surcharge": 250.00},
    "Air":    {"per_mile": 4.75, "mph": 480, "surcharge": 120.00},
    "Parcel": {"per_mile": 1.40, "mph": 45,  "surcharge": 12.00},
}

WEIGHT_BREAK_LBS = 500       # shipments over this get a per-lb surcharge
PER_LB_OVER_BREAK = 0.18


class UnknownCityError(ValueError):
    pass


class UnknownModeError(ValueError):
    pass


def _normalize(city: str) -> str:
    return city.strip().lower()


def _display_city(city: str) -> str:
    """Title-case a city name but keep 2-letter state codes uppercase
    ('orlando, fl' -> 'Orlando, FL', not 'Orlando, Fl')."""
    return ", ".join(
        part.strip().upper() if len(part.strip()) == 2 else part.strip().title()
        for part in city.split(",")
    )


def known_cities():
    return sorted(_display_city(c) for c in CITY_COORDS)


def known_modes():
    return sorted(MODE_PROFILE)


def haversine_miles(origin: str, destination: str) -> float:
    o, d = _normalize(origin), _normalize(destination)
    if o not in CITY_COORDS:
        raise UnknownCityError(f"Unknown origin city: {origin!r}")
    if d not in CITY_COORDS:
        raise UnknownCityError(f"Unknown destination city: {destination!r}")

    lat1, lon1 = CITY_COORDS[o]
    lat2, lon2 = CITY_COORDS[d]
    R = 3958.8  # earth radius, miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def quote(origin: str, destination: str, mode: str, weight_lbs: float, ship_date: date = None):
    if mode not in MODE_PROFILE:
        raise UnknownModeError(f"Unknown mode: {mode!r}. Choose from {known_modes()}")
    if weight_lbs is None or weight_lbs <= 0:
        raise ValueError("weight_lbs must be a positive number")

    profile = MODE_PROFILE[mode]
    distance = haversine_miles(origin, destination)
    # road/rail distance is never a straight line — pad the great-circle distance
    road_factor = {"Truck": 1.18, "Rail": 1.22, "Ocean": 1.05, "Air": 1.0, "Parcel": 1.18}[mode]
    distance = distance * road_factor

    base_cost = distance * profile["per_mile"]
    weight_cost = max(0, weight_lbs - WEIGHT_BREAK_LBS) * PER_LB_OVER_BREAK
    total_cost = round(base_cost + weight_cost + profile["surcharge"], 2)

    transit_hours = distance / profile["mph"]
    handling_hours = {"Truck": 4, "Rail": 10, "Ocean": 30, "Air": 6, "Parcel": 5}[mode]
    transit_days = max(1, math.ceil((transit_hours + handling_hours) / 24))

    ship_date = ship_date or date.today()
    eta = ship_date + timedelta(days=transit_days)

    return {
        "origin": _display_city(origin),
        "destination": _display_city(destination),
        "mode": mode,
        "weight_lbs": weight_lbs,
        "distance_miles": round(distance, 1),
        "estimated_cost_usd": total_cost,
        "estimated_transit_days": transit_days,
        "ship_date": ship_date.isoformat(),
        "estimated_delivery": eta.isoformat(),
    }
