
import csv
import os
import re
import math

from pathlib import Path
from functools import lru_cache
from collections import defaultdict
from statistics import median


def clean_key(value):
    return re.sub(r"[^a-z0-9]", "", value.lower())


@lru_cache(maxsize=4)
def load_postal_index(path, modified):
    index = defaultdict(list)

    with open(path, encoding="utf-8-sig", newline="") as f:
        for record in csv.DictReader(f):
            row = {
                clean_key(k): str(v or "").strip()
                for k, v in record.items()
                if k
            }

            pin = row.get("pincode") or row.get("pin")

            if not re.fullmatch(r"[1-9][0-9]{5}", pin or ""):
                continue

            name = (
                row.get("officename")
                or row.get("locality")
                or row.get("postofficename")
                or ""
            )

            district = row.get("district", "")
            state = row.get("statename") or row.get("state", "")

            lat = lon = None

            try:
                a = float(row.get("latitude", ""))
                b = float(row.get("longitude", ""))

                if (
                    math.isfinite(a)
                    and math.isfinite(b)
                    and 6 <= a <= 38
                    and 68 <= b <= 98
                ):
                    lat, lon = a, b

            except (ValueError, TypeError):
                pass

            index[pin].append({
                "name": name,
                "district": district,
                "state": state,
                "latitude": lat,
                "longitude": lon
            })

    return dict(index)


def postal_index():
    path = Path(os.getenv(
        "REGEN_POSTAL_DATASET",
        str(Path.home() / "regen-infra" / "india-postal.csv")
    ))

    if not path.is_file():
        return {}

    return load_postal_index(
        str(path.resolve()),
        path.stat().st_mtime_ns
    )


def lookup_postal(pin):
    pin = str(pin or "").strip()

    if not re.fullmatch(r"[1-9][0-9]{5}", pin):
        return {"status": "invalid_pin"}

    index = postal_index()

    if not index:
        return {"status": "dataset_missing"}

    rows = index.get(pin, [])

    if not rows:
        return {"status": "not_found", "pin": pin}

    names = sorted({
        r["name"] for r in rows if r["name"]
    })

    districts = sorted({
        r["district"] for r in rows if r["district"]
    })

    states = sorted({
        r["state"] for r in rows if r["state"]
    })

    locality = ", ".join(dict.fromkeys([
        *names[:3], *districts, *states, "India"
    ]))

    result = {
        "status": "found",
        "pin": pin,
        "locality": locality,
        "districts": districts,
        "states": states,
        "source": "India postal dataset",
        "coordinate_basis": None
    }

    points = [
        (r["latitude"], r["longitude"])
        for r in rows
        if r["latitude"] is not None
    ]

    if points:
        result.update({
            "latitude": median(p[0] for p in points),
            "longitude": median(p[1] for p in points),
            "coordinate_basis": "postal_office_median"
        })

    return result


def geographic_context(pin):
    result = lookup_postal(pin)

    if result.get("status") != "found":
        return {
            "local": str(pin or "India"),
            "regional": "India",
            "districts": [],
            "states": []
        }

    districts = result.get("districts", [])
    states = result.get("states", [])

    return {
        "local": f"{result['locality']} {pin}",
        "regional": ", ".join(dict.fromkeys([
            *districts, *states, "India"
        ])),
        "districts": districts,
        "states": states
    }
