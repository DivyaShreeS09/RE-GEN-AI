"""Optional public geographic discovery.

Public listings are leads, not verified accepting partners.
No API keys or precise user location required.
"""

import os
import re
import time
import threading
import math
from contextvars import ContextVar

import httpx

_LOCK = threading.Lock()
_CACHE = {}
_LAST_REQUEST = 0.0
_TTL = 86400
_MAX_CACHE = 256


research_deadline = ContextVar("research_deadline", default=float("inf"))


def research_remaining():
    return research_deadline.get() - time.monotonic()


class ResearchDeadlineExceeded(httpx.TimeoutException):
    pass


def check_research_deadline():
    if research_remaining() <= 0:
        raise ResearchDeadlineExceeded("Optional research deadline reached.")


def research_timeout():
    check_research_deadline()
    remaining = research_remaining()
    return httpx.Timeout(min(1.5, remaining), connect=min(1.0, remaining))


def cached(key, loader, *, annotate=False):
    with _LOCK:
        entry = _CACHE.get(key)

        if entry and time.monotonic() < entry[0]:
            return {**entry[1], "cache_hit": True} if annotate else entry[1]

    result = loader()

    if result.get("status") in {"budget_exhausted", "deadline_reached"}:
        return {**result, "cache_hit": False} if annotate else result

    ttl = _TTL if result.get("status") in {"found", "not_found", "no_results"} else 30
    with _LOCK:
        if len(_CACHE) >= _MAX_CACHE:
            _CACHE.pop(min(_CACHE, key=lambda k: _CACHE[k][0]), None)
        _CACHE[key] = (time.monotonic() + ttl, result)

    return {**result, "cache_hit": False} if annotate else result


def enabled():
    return (
        os.getenv("REGEN_ENV") != "test"
        and os.getenv("REGEN_PUBLIC_DISCOVERY") == "1"
        and bool(os.getenv("REGEN_RESEARCH_CONTACT"))
    )


def provider_url(setting, default):
    from urllib.parse import urlsplit
    raw = os.getenv(setting) or default
    url = urlsplit(raw)
    if url.scheme != "https" or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError("Invalid discovery endpoint.")
    return raw


def request_public(url, params):
    global _LAST_REQUEST

    with _LOCK:
        delay = 1.1 - (
            time.monotonic() - _LAST_REQUEST
        )

        if delay > 0:
            time.sleep(delay)

        _LAST_REQUEST = time.monotonic()

        with httpx.Client(
            timeout=httpx.Timeout(
                6.0, connect=2.0
            ),
            follow_redirects=False,
            trust_env=False,
            headers={
                "User-Agent": (
                    "REGEN-AI/1.0 "
                    + os.environ["REGEN_RESEARCH_CONTACT"]
                )
            },
        ) as client:
            response = client.get(
                url, params=params
            )
            response.raise_for_status()
            return response.json()


def resolve_pin(pin):
    pin = str(pin or "").strip()

    if not re.fullmatch(r"[1-9][0-9]{5}", pin):
        return {"status": "invalid_pin"}

    from core.postal_intelligence import lookup_postal

    local = lookup_postal(pin)

    if (
        local.get("status") == "found"
        and local.get("latitude") is not None
        and local.get("longitude") is not None
    ):
        return local

    if not enabled():
        return {
            **local,
            "status": (
                "coordinates_unavailable"
                if local.get("status") == "found"
                else local.get("status")
            )
        }

    def lookup():
        try:
            rows = request_public(
                provider_url("REGEN_NOMINATIM_URL", "https://nominatim.openstreetmap.org/search"),
                {
                    "postalcode": pin,
                    "countrycodes": "in",
                    "format": "jsonv2",
                    "addressdetails": 1,
                    "limit": 5,
                },
            )

            for row in rows:
                address = row.get("address", {})

                if address.get("country_code") != "in":
                    continue

                if address.get("postcode") != pin:
                    continue

                lat = float(row["lat"])
                lon = float(row["lon"])

                if not (
                    math.isfinite(lat)
                    and math.isfinite(lon)
                    and -90 <= lat <= 90
                    and -180 <= lon <= 180
                ):
                    continue

                return {
                    "status": "found",
                    "pin": pin,
                    "latitude": lat,
                    "longitude": lon,
                    "locality": row.get("display_name"),
                    "source": "OpenStreetMap Nominatim",
                }

            return {"status": "not_found"}

        except (
            httpx.HTTPError,
            ValueError,
            TypeError,
            KeyError,
        ):
            return {"status": "unavailable"}

    return cached(("pin", os.getenv("REGEN_NOMINATIM_URL"), pin), lookup)


# Fixed geographic categories, not fixed material answers.
# The planner may select only these supported categories.

FILTERS = {
    "recycling": '["amenity"="recycling"]',
    "scrap": '["shop"="scrap"]',
    "second_hand": '["shop"="second_hand"]',
    "charity": '["shop"="charity"]',
    "tailoring": '["craft"="tailor"]',
    "repair": '["craft"="electronics_repair"]',
    "waste_transfer": '["amenity"="waste_transfer_station"]',
}


def distance_km(lat1, lon1, lat2, lon2):
    a1, a2 = map(math.radians, (lat1, lat2))
    dlat = a2 - a1
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(a1)
        * math.cos(a2)
        * math.sin(dlon / 2) ** 2
    )

    return round(
        6371 * 2 * math.asin(
            math.sqrt(min(1.0, max(0.0, a)))
        ),
        1,
    )


def discover_services(pin, categories, intents=()):
    if not enabled():
        status = "disabled"
        if os.getenv("REGEN_ENV") != "test" and os.getenv("REGEN_PUBLIC_DISCOVERY") == "1":
            status = "research_contact_required"
        return {"status": status, "services": []}

    location = resolve_pin(pin)

    if location["status"] != "found":
        return {
            "status": "postal_provider_unavailable" if location["status"] == "unavailable" else location["status"],
            "services": [],
        }

    categories = sorted({
        category for category in categories
        if category in FILTERS
    })

    if not categories:
        return {
            "status": "no_supported_categories",
            "services": [],
        }

    lat = location["latitude"]
    lon = location["longitude"]

    # Only fixed vocabulary reaches the public endpoint, never free-text inventory.
    filters = {
        "books": "books?|textbooks?|literature",
        "textiles": "clothes|clothing|textiles?|garments?",
        "electronics": "electronics?|phones?|mobiles?|ewaste|e-waste",
        "paper": "paper|cardboard",
    }
    intents = tuple(sorted(set(intents) & filters.keys()))
    material_filter = "|".join(filters[key] for key in intents)

    def lookup_radius(radius):
        clauses = "".join(
            f'nwr(around:{radius},{lat},{lon})'
            f'{FILTERS[category]}{qualifier};'
            for category in categories
            for qualifier in (
                (f'["description"~"{material_filter}",i]', f'["name"~"{material_filter}",i]',
                 *(f'["recycling:{key}"="yes"]' for key in intents if key in {"paper", "books", "clothes", "electronics"}))
                if material_filter else ("",)
            )
        )

        query = (
            "[out:json][timeout:5];"
            f"({clauses});"
            "out center 80;"
        )

        try:
            data = request_public(
                provider_url("REGEN_OVERPASS_URL", "https://overpass-api.de/api/interpreter"),
                {"data": query},
            )

        except (
            httpx.HTTPError,
            ValueError,
            TypeError,
        ):
            return {
                "status": "unavailable",
                "services": [],
            }

        services = []
        seen = set()

        for element in data.get("elements", []):
            tags = element.get("tags", {})
            name = str(tags.get("name", "")).strip()

            if not name:
                continue

            kind = element.get("type")
            osm_id = element.get("id")

            if kind not in ("node", "way", "relation"):
                continue

            if not isinstance(osm_id, int):
                continue

            if (kind, osm_id) in seen:
                continue

            seen.add((kind, osm_id))

            center = element.get("center", element)

            try:
                slat = float(center["lat"])
                slon = float(center["lon"])

                if not (
                    -90 <= slat <= 90
                    and -180 <= slon <= 180
                ):
                    continue

            except (
                KeyError, TypeError, ValueError
            ):
                continue

            distance = distance_km(lat, lon, slat, slon)

            if distance > radius / 1000:
                continue

            services.append({
                "latitude": slat,
                "longitude": slon,
                "distance_basis": "postal_centroid_straight_line",
                "maps_url": (
                    "https://www.google.com/maps/search/?api=1"
                    f"&query={slat},{slon}"
                ),
                "organization": name[:200],
                "description": str(tags.get("description", ""))[:300],
                "distance_km": distance_km(
                    lat, lon, slat, slon
                ),
                "category": (
                    tags.get("shop")
                    or tags.get("craft")
                    or tags.get("amenity")
                ),
                "material_tags": [
                    key.removeprefix("recycling:")
                    for key, value in tags.items()
                    if key.startswith("recycling:")
                    and value == "yes"
                ],
                "source_url": (
                    "https://www.openstreetmap.org/"
                    f"{kind}/{osm_id}"
                ),
                "verification": "public_unverified",
                "acceptance_confirmed": False,
                "pickup_confirmed": False,
                "source": "OpenStreetMap contributors",
            })

        services.sort(
            key=lambda row: row["distance_km"]
        )

        return {
            "status": (
                "found" if services else "no_results"
            ),
            "locality": location["locality"],
            "postal_coordinates": {
                "latitude": lat,
                "longitude": lon
            },
            "search_radius_km": radius / 1000,
            "services": services[:20],
            "attribution": (
                "OpenStreetMap contributors, ODbL"
            ),
        }

    def lookup():
        for radius in (5000, 10000, 25000, 50000):
            result = lookup_radius(radius)

            if result["status"] == "unavailable":
                return result

            if result["services"]:
                return result

        return result

    return cached(
        ("services-v2", os.getenv("REGEN_OVERPASS_URL"), os.getenv("REGEN_NOMINATIM_URL"), pin, tuple(categories), intents),
        lookup, annotate=True,
    )
