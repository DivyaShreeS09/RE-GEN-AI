"""Reviewed market evidence catalogue."""

import json
import os
import re
from pathlib import Path
from datetime import date
from functools import lru_cache

from core.market_valuation import (
    value_pathway,
    convert_quantity, number,
)

DEFAULT_PATH = (
    Path.home()
    / "regen-infra"
    / "market-evidence.json"
)


@lru_cache(maxsize=1)
def published_references():
    return json.loads((Path(__file__).resolve().parents[1] / "data" / "recovery_references.json").read_text(encoding="utf-8"))


def normalize(value):
    return re.sub(
        r"\s+", " ", str(value or "").strip()
    ).casefold()


def load_catalogue():
    path = Path(
        os.getenv("REGEN_MARKET_EVIDENCE_FILE") or DEFAULT_PATH
    )

    try:
        if path.stat().st_size > 5_000_000:
            return []

        data = json.loads(
            path.read_text(encoding="utf-8-sig")
        )

        if not isinstance(data, list):
            return []

        return [
            row for row in data
            if isinstance(row, dict)
            and row.get("reviewed") is True
        ]

    except (OSError, ValueError):
        return []


def _find_market_evidence_exact(item, pathway, pin=None, *, rows=None):
    material = normalize(item.get("material"))
    condition = normalize(item.get("condition"))
    category = pathway.get("category")

    candidates = []

    for row in (load_catalogue() if rows is None else rows):
        if pin and re.fullmatch(r"600\d{3}", pin):
            if row.get("evidence_type") == "out_of_area_price_reference":
                continue

        names = [row.get("material", "")]

        aliases = row.get("aliases", [])
        if isinstance(aliases, list):
            names.extend(aliases)

        normalized_names = {normalize(name) for name in names}
        conditional_grade = None

        if material not in normalized_names:
            if (
                material in {
                    "plastic bottle", "plastic bottles",
                    "water bottles", "juice bottles",
                    "beverage bottles"
                }
                and normalize(row.get("material")) == "pet bottles"
            ):
                conditional_grade = "Applicable only to confirmed PET bottles."
            else:
                continue

        conditions = row.get("conditions")
        if not isinstance(conditions, list):
            conditions = [row.get("condition")]
        if condition not in {normalize(value) for value in conditions if isinstance(value, str)}:
            continue

        evidence_category = row.get("category")
        gross_reference = (
            row.get("value_type", "gross_reference")
            == "gross_reference"
        )

        compatible_scrap_reference = (
            gross_reference
            and evidence_category in {"sell", "recycle"}
            and category in {"sell", "recycle", "collective"}
            and row.get("evidence_type") in {
                "published_buying_rate",
                "indexed_published_buying_rate",
                "out_of_area_price_reference",
            }
        )

        collective_reference = (
            compatible_scrap_reference
            and category == "collective"
        )

        if evidence_category != category and not compatible_scrap_reference:
            continue

        from core.market_valuation import quantity_range
        quantities = quantity_range(item, row)
        quantity_low, quantity_high = quantities or (None, None)

        try:
            observed = date.fromisoformat(
                row["observed_on"]
            )
        except (KeyError, TypeError, ValueError):
            continue

        age = (date.today() - observed).days

        max_age = 730 if row.get("evidence_type") == "historical_proposed_rate" else 365
        if age < 0 or age > max_age:
            continue

        lower = row.get("minimum_quantity")
        upper = row.get("maximum_quantity")
        if quantities is not None and (
            (lower is not None and (number(lower) is None or quantity_low < number(lower)))
            or (upper is not None and (number(upper) is None or quantity_high > number(upper)))
        ):
            continue
        pins = row.get("service_pins", [])

        if not isinstance(pins, list):
            continue

        exact_locality = bool(pin and pin in pins)

        if pins and not exact_locality:
            continue

        if not pins and row.get("scope") not in {"India", "regional_benchmark"}:
            continue

        evidence = dict(row)

        if compatible_scrap_reference and evidence_category != category:
            evidence["category"] = category
            evidence.pop("costs_inr", None)

        evidence["material"] = item["material"]
        evidence["condition"] = item["condition"]

        valuation = value_pathway(
            item, pathway, evidence
        )

        if valuation.get("status") not in {"estimated", "rate_only"}:
            continue

        if collective_reference:
            valuation["reason"] = (
                "Indicative value of this material's contribution "
                "to collective recovery. Group minimums, transport "
                "and collection costs require confirmation."
            )

        valuation["evidence_type"] = row.get("evidence_type", "published_reference")
        valuation["provenance"] = row.get("provenance", "reviewed_reference")
        valuation["applicability"] = " ".join(filter(None, (
            conditional_grade,
            row.get("applicability")
        )))

        if conditional_grade:
            valuation["conditional_grade"] = True
            valuation["status"] = "rate_only"
            valuation["minimum_inr"] = None
            valuation["maximum_inr"] = None
            valuation["net_minimum_inr"] = None
            valuation["net_maximum_inr"] = None
            valuation["clarification"] = (
                "Confirm PET polymer grade and eligible dry weight."
            )
        valuation["geographic_basis"] = ("regional_reference" if row.get("scope") in {"regional", "regional_benchmark"} else
            "local_reference"
            if exact_locality
            else "national_reference"
        )

        historical = age > 90 or valuation["evidence_type"] == "historical_proposed_rate"
        scope = {"local_reference":3, "regional_reference":2, "national_reference":1}[valuation["geographic_basis"]]
        candidates.append((
            (valuation["status"] == "estimated", scope, not historical, valuation["provenance"] in {"live_research", "cached_research"}),
            observed,
            valuation,
        ))

    if not candidates:
        return None

    candidates.sort(
        key=lambda entry: (entry[0], entry[1]),
        reverse=True,
    )

    return candidates[0][2]



def find_market_evidence(item, pathway, pin=None, *, rows=None):
    """Use semantic identity without converting inference into a quote."""

    exact = _find_market_evidence_exact(
        item, pathway, pin, rows=rows
    )

    if exact:
        return exact

    identity = item.get("material_identity") or {}

    if (
        not identity
        or identity.get("certainty") == "unknown"
        or item.get("contaminated")
        or item.get("condition") in {"contaminated", "spoiled"}
    ):
        return None

    from core.waste_intelligence import restricted_material

    original = item.get("material", "")

    candidates = list(dict.fromkeys([
        identity.get("canonical_material", ""),
        identity.get("search_material", "")
    ]))

    for candidate in candidates:
        if (
            not candidate
            or normalize(candidate) == normalize(original)
            or restricted_material(candidate, {})
            or restricted_material(original, {})
        ):
            continue

        normalized_item = {
            **item,
            "material": candidate
        }

        valuation = _find_market_evidence_exact(
            normalized_item, pathway, pin, rows=rows
        )

        if not valuation:
            continue

        valuation = dict(valuation)

        valuation["semantic_match"] = True
        valuation["matched_material"] = candidate
        valuation["original_material"] = original

        # Semantic similarity alone cannot establish
        # physical grade or commercial eligibility.

        valuation["status"] = "rate_only"
        valuation["conditional_grade"] = True

        for key in (
            "minimum_inr",
            "maximum_inr",
            "net_minimum_inr",
            "net_maximum_inr"
        ):
            valuation[key] = None

        valuation["clarification"] = (
            identity.get("clarification")
            or "Confirm material composition and commercial grade."
        )

        valuation["applicability"] = " ".join(filter(None, [
            valuation.get("applicability"),
            "Semantic reference match only. Confirm the material, "
            "grade, eligible quantity and buyer acceptance."
        ]))

        return valuation

    return None




def configured_market_feed():
    """Fetch an operator-approved structured feed without sending inventory data."""
    from urllib.parse import urlsplit
    import httpx
    from core.public_discovery import cached, check_research_deadline, research_timeout

    endpoint = os.getenv("REGEN_MARKET_FEED_URL", "")
    if os.getenv("REGEN_ENV") == "test" or not endpoint:
        return []
    try:
        url = urlsplit(endpoint)
        if url.scheme != "https" or not url.hostname or url.username or url.password or url.query or url.fragment:
            return []
    except ValueError:
        return []

    def download():
        try:
            with httpx.Client(timeout=research_timeout(), trust_env=False, follow_redirects=False) as client:
                with client.stream("GET", endpoint) as response:
                    response.raise_for_status()
                    buffer = bytearray()
                    for block in response.iter_bytes():
                        check_research_deadline()
                        buffer.extend(block)
                        if len(buffer) > 1_000_000:
                            return {"rows": []}
            rows = json.loads(buffer)
            return {"status": "found", "rows": [row for row in rows if isinstance(row, dict)
                              and row.get("reviewed") is True] if isinstance(rows, list) else []}
        except (httpx.HTTPError, ValueError):
            return {"rows": []}

    return cached(("market-feed", endpoint), download)["rows"]


ISS_RATE_URL = "https://issindustries.in/sell-coconut-shell"


def fetch_public_bytes(url, *, params=None):
    import httpx
    from core.public_discovery import check_research_deadline, research_timeout

    with httpx.Client(timeout=research_timeout(), trust_env=False, follow_redirects=False,
                      headers={"User-Agent": "REGEN-AI public recovery evidence/1.0"}) as client:
        with client.stream("GET", url, params=params) as response:
            response.raise_for_status()
            buffer = bytearray()
            for block in response.iter_bytes():
                check_research_deadline()
                buffer.extend(block)
                if len(buffer) > 1_000_000:
                    raise ValueError("Public evidence response too large.")
            return bytes(buffer)


def parse_iss_shell_rate(document):
    from datetime import datetime
    from html import unescape
    block = re.search(r"<!-- product-rate:start -->(.*?)</table>", document, re.S)
    if not block:
        return None
    text = unescape(re.sub(r"<[^>]+>", " ", block[1]))
    day = re.search(r"\b(\d{1,2} [A-Z][a-z]{2} \d{4})\s*·\s*Kangayam market rate", text)
    quote = re.search(r"Coconut shell\s*₹\s*(\d{1,3}(?:\.\d{1,2})?)\s*/kg", text)
    if not day or not quote:
        return None
    observed = datetime.strptime(day[1], "%d %b %Y").date()
    if not 0 <= (date.today() - observed).days <= 14:
        return None
    return dict(material="coconut shell", aliases=["coconut shells"], category="sell", unit="kg",
                reviewed=True, conditions=["used", "dry", "good"], scope="regional_benchmark",
                locality="Kangayam, Tamil Nadu", observed_on=observed.isoformat(), source_url=ISS_RATE_URL,
                evidence_type="published_buying_rate", rate_min_inr=quote[1], rate_max_inr=quote[1],
                applicability="Kangayam indicative buying rate for eligible shells. Confirm grade, eligible weight, lot minimum and transport.")


KABADIFY_RATE_URL = "https://kabadify.com/rates.json"
KABADIFY_AREA_URL = "https://kabadify.com/about"
KABADIFY_PINS = ("560078", "560041", "560011", "560029", "560076")


def kabadify_rates(data):
    if (not isinstance(data, dict) or data.get("company") != "Kabadify"
            or data.get("currency") != "INR" or data.get("source") != "ops-published"
            or not isinstance(data.get("license"), dict)
            or data["license"].get("url") != "https://creativecommons.org/licenses/by/4.0/"):
        return []
    area = data.get("serviceArea", "")
    if not isinstance(area, str) or not all(name in area for name in ("JP Nagar", "Jayanagar", "BTM Layout", "Bilekahalli")):
        return []
    effective = data.get("effectiveFrom")
    if not isinstance(effective, str):
        return []
    observed = date.fromisoformat(effective[:10])
    if not 0 <= (date.today() - observed).days <= 180:
        return []
    entries = data.get("items")
    if not isinstance(entries, list):
        return []
    aliases = {
        "newspaper": ["newspapers", "old newspaper", "old newspapers"],
        "books": ["old books", "used books"], "carton": ["cartons", "carton boxes", "cardboard", "corrugated cardboard"],
        "pet_bottle": ["pet bottles"], "clothes": ["old clothes", "used clothes", "discarded clothes"],
        "aluminium_can": ["aluminium cans", "aluminum cans"], "office_paper": ["used office paper"],
    }
    rows = []
    for entry in entries[:100]:
        if (not isinstance(entry, dict) or entry.get("hazardous") is not False
                or entry.get("pricingMode") != "per_kg" or entry.get("unit") != "INR/kg"
                or entry.get("category") not in {"paper", "plastic", "metal", "other"}):
            continue
        identifier, label, rate = (entry.get(key) for key in ("id", "name", "rate"))
        if (not isinstance(identifier, str) or not re.fullmatch(r"[a-z_]{2,45}", identifier)
                or not isinstance(label, str) or not re.fullmatch(r"[A-Za-z -]{2,65}", label)
                or number(rate) is None):
            continue
        rows.append({"material": label, "aliases": aliases.get(identifier, []), "category": "recycle", "unit": "kg",
                     "conditions": ["dry", "used", "good"] + (["mixed"] if identifier == "mixed_plastic" else []),
                     "reviewed": True, "locality": "Published Bengaluru service area", "service_pins": list(KABADIFY_PINS),
                     "observed_on": observed.isoformat(), "source_url": "https://kabadify.com/rates#" + identifier,
                     "rate_min_inr": rate, "rate_max_inr": rate, "evidence_type": "published_buying_rate",
                     "applicability": "Kabadify, CC BY 4.0. Gross payout for accepted weight and grade. Pickup minimums and fees depend on the order."})
    return rows


def public_market_research(items, pin):
    from urllib.parse import urlsplit
    from core.public_discovery import cached

    if os.getenv("REGEN_ENV") == "test":
        return {"rows": [], "services": [], "status": "offline"}
    rows, services, statuses = [], [], []
    materials = tuple(sorted({normalize(item.material) for item in items
                              if re.fullmatch(r"[A-Za-z][A-Za-z -]{1,49}", item.material)}))
    if os.getenv("REGEN_PUBLIC_MARKET_RESEARCH") == "1" and set(materials) & {"coconut shell", "coconut shells"}:
        def read_iss():
            document = fetch_public_bytes(ISS_RATE_URL).decode("utf8")
            row = parse_iss_shell_rate(document)
            return {"status": "found" if row else "no_results", "rows": [row] if row else [], "services": []}
        endpoint = ("iss-buying-rate", ISS_RATE_URL)
        result = research_result(cached, endpoint, read_iss)
        rows.extend(result["rows"])
        statuses.append(result["status"])
        if pin in {"638701", "638702"} and result["rows"]:
            services.append(dict(organization="ISS INDUSTRIES", locality="Kangayam, Tamil Nadu",
                material="coconut shell", aliases=["coconut shells"], pathways=["sell"], service_pins=["638701"],
                source_url=ISS_RATE_URL, description="Publishes coconut shell purchasing at its Kangayam yard. Pickup and lot suitability require confirmation.",
                provenance=result["rows"][0]["provenance"], reviewed_on=result["rows"][0]["observed_on"]))
    if os.getenv("REGEN_PUBLIC_MARKET_RESEARCH") == "1" and materials:
        def read_kabadify():
            matches = kabadify_rates(json.loads(fetch_public_bytes(KABADIFY_RATE_URL)))
            return {"status": "found" if matches else "no_results", "rows": matches, "services": []}
        result = research_result(cached, ("kabadify-rates", KABADIFY_RATE_URL), read_kabadify)
        statuses.append(result["status"])
        matched = [row for row in result["rows"] if set(materials).intersection(
            normalize(label) for label in [row["material"], *row["aliases"]])]
        if pin in KABADIFY_PINS:
            rows.extend(matched)
        else:
            for row in matched:
                rows.append({
                    **row,
                    "service_pins": [],
                    "scope": "regional_benchmark",
                    "evidence_type": "out_of_area_price_reference",
                    "applicability": (
                        "Published Bengaluru comparison rate, "
                        "not a local quotation. Actual local prices, "
                        "acceptance and collection costs may differ."
                    ),
                })

        for row in matched if pin in KABADIFY_PINS else []:
            services.append({"organization": "Kabadify", "locality": "Bengaluru", "material": row["material"],
                             "aliases": row["aliases"], "pathways": ["recycle"], "conditions": row["conditions"],
                             "service_pins": list(KABADIFY_PINS), "source_url": KABADIFY_AREA_URL,
                             "description": "The publisher advertises scrap collection for this material class and lists this PIN. Order minimum, grade and pickup fees require confirmation.",
                             "provenance": row["provenance"], "reviewed_on": row["observed_on"]})
    url = os.getenv("REGEN_MATERIAL_RESEARCH_URL", "")
    if url and materials:
        try:
            parsed = urlsplit(url)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ValueError("Invalid research URL.")
        except ValueError:
            statuses.append("invalid_configuration")
        else:
            def query_provider():
                response = json.loads(fetch_public_bytes(url, params={"materials": ",".join(materials), "pin": pin or ""}))
                if not isinstance(response, dict):
                    raise ValueError("Invalid research response.")
                rates = response.get("rates", [])
                leads = response.get("services", [])
                if not isinstance(rates, list) or not isinstance(leads, list):
                    raise ValueError("Invalid research response.")
                return {"status": "found" if rates or leads else "no_results",
                        "rows": [row for row in rates[:100] if isinstance(row, dict) and row.get("reviewed") is True],
                        "services": [row for row in leads[:100] if isinstance(row, dict)]}
            result = research_result(cached, ("material-research", url, materials, pin), query_provider)
            rows.extend(result["rows"])
            services.extend(result["services"])
            statuses.append(result["status"])
    return {"rows": rows, "services": services,
            "status": "found" if rows or services else (statuses[-1] if statuses else "source_not_configured")}


def research_result(cache, key, loader):
    import httpx
    from core.public_discovery import research_remaining

    def load():
        try:
            return loader()
        except (httpx.HTTPError, ValueError, TypeError):
            return {"status": "deadline_reached" if research_remaining() <= 0 else "unavailable", "rows": [], "services": []}

    data = cache(key, load, annotate=True)
    origin = "cached_research" if data["cache_hit"] else "live_research"
    return {**data, **{field: [{**row, "provenance": origin} for row in data[field]] for field in ("rows", "services")}}


def inventory_market_rows(*, remote=False):
    return published_references()["market"] + load_catalogue() + (configured_market_feed() if remote else [])


def compatible_market_pathways(item, pin, rows):
    allowed = {"sell", "reuse", "repair", "upcycle", "recycle", "compost", "collective",
               "industrial_symbiosis", "professional"}
    categories = dict.fromkeys(row.get("category") for row in rows if isinstance(row.get("category"), str))
    return [category for category in categories if category in allowed
            and find_market_evidence(item, {"category": category}, pin, rows=rows)]


def attach_market_evidence(item, intelligence, pin=None, *, rows=None):
    rows = load_catalogue() if rows is None else rows
    for route in intelligence.get("pathways", []):
        existing = route.get("valuation") or {}

        if existing.get("status") in (
            "estimated", "non_commercial"
        ):
            continue

        estimate = find_market_evidence(
            item, route, pin, rows=rows
        )

        if estimate is not None:
            route["valuation"] = estimate

    return intelligence
