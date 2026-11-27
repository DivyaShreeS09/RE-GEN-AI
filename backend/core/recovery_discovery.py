"""Pathway-specific recovery service discovery."""

from core.postal_intelligence import geographic_context

from core.public_discovery import check_research_deadline, research_timeout
from core.market_evidence import normalize, published_references
from core.market_valuation import convert_quantity, number
from urllib.parse import urlsplit
import re
import json


CATEGORY_MAP = {
    "sell": {"scrap", "second_hand"},
    "donate": {"charity"},
    "reuse": {"second_hand"},
    "repair": {"repair", "electronics_repair"},
    "upcycle": {"tailoring", "tailor"},
    "recycle": {"recycling", "scrap"},
    "compost": {"recycling"},
    "collective": {"recycling", "scrap"},
    "industrial_symbiosis": {"recycling", "scrap"},
    "professional": {"waste_transfer", "waste_transfer_station"},
}

def relevant_listing(item, pathway, service):
    """Use explicit recycling tags or material-specific business descriptions."""
    material = set(re.findall(r"[a-z0-9]{3,}", item["material"].casefold()))
    material -= {"old", "used", "broken", "damaged", "mixed", "good", "pieces"}
    tags = set(re.findall(r"[a-z0-9]{3,}", " ".join(service.get("material_tags", [])).casefold()))
    description = " ".join([service["organization"], service.get("description", "")]).casefold()
    if pathway in {"recycle", "collective", "industrial_symbiosis"} and material & tags:
        return True
    words = set(re.findall(r"[a-z0-9]{3,}", description))
    if not material & words:
        return False
    intent = {
        "sell": r"\b(buy|buyer|buyers|buyback|buy-back|purchase|purchasing|we buy)\b",
        "professional": r"\b(recycling|recycler|waste recovery|treatment)\b",
        "repair": r"\b(repair|refurbishment)\b",
        "donate": r"\b(donation|donations|accepts donated)\b",
        "recycle": r"\b(recycling|recycler)\b",
        "collective": r"\b(collection|collects)\b",
        "industrial_symbiosis": r"\b(buyer|processor|purchasing|feedstock)\b",
        "compost": r"\b(composting|compost)\b",
    }
    return bool(pathway in intent and re.search(intent[pathway], description))


def published_service_leads(item, pin, category):
    if item.get("contaminated"):
        return []
    districts = {normalize(name) for name in geographic_context(pin)["districts"]}
    names = (item["material"], item.get("original_material", ""))
    labels = [label for name in names if name for label in (name, f"waste {name}")]
    matches = []
    for lead in published_references()["services"]:
        exact = pin in lead.get("service_pins", [])
        city = normalize(lead.get("coverage_city")) in districts
        if not (exact or city) or category not in lead["pathways"]:
            continue
        if not any(re.search(r"\b(?:" + lead["material_pattern"] + r")\b", label, re.I) for label in labels):
            continue
        conditions = lead.get("conditions")
        if conditions and normalize(item.get("condition")) not in {normalize(value) for value in conditions}:
            continue
        matches.append({
            **{key: lead[key] for key in ("organization", "locality", "description", "source_url", "reviewed_on")},
            "verification": "public_unverified", "source": "Organization website",
            "acceptance_confirmed": False, "provenance": "reviewed_reference",
            "coverage": "documented_region" if city and not exact else "reviewed_pin_reference",
            "publisher_evidence": lead["description"],
        })
    return matches


SERVICE_TERMS = {
    "sell": "used goods buyers buyback",
    "repair": "repair refurbishment services",
    "reuse": "reuse exchange programmes",
    "donate": "donation collection charities",
    "upcycle": "upcycling workshops",
    "recycle": "material recyclers doorstep scrap collectors",
    "compost": "managed composting facilities",
    "collective": "doorstep collectors group pickup",
    "industrial_symbiosis": "industrial feedstock buyers processors",
    "professional": "authorized specialist recovery services",
}


def map_search_terms(material, category):
    m = material.casefold()

    if re.search(r"\b(hair|keratin)\b", m):
        return "human hair procurement"

    if category == "donate":
        if re.search(r"\b(books?|textbooks?)\b", m):
            return "book donation collection"
        if re.search(r"\b(clothes|clothing|garments?|sarees?)\b", m):
            return "used clothes donation"
        return f"{material} donation collection"

    if re.search(r"\b(books?|textbooks?)\b", m):
        if category in {"sell", "reuse"}:
            return "second hand book buyers"

    commercial = {
        "sell", "recycle", "collective", "industrial_symbiosis"
    }

    if category in commercial:
        if "glass" in m:
            return "glass scrap dealers"
        if re.search(r"\b(cans?|aluminium|aluminum)\b", m):
            return "metal scrap dealers"
        if re.search(r"\b(plastic|pet)\b", m):
            return "plastic scrap dealers"
        if re.search(r"\b(paper|cardboard|newspapers?)\b", m):
            return "paper scrap dealers"

    purposes = {
        "sell": "buyers",
        "reuse": "reuse programme",
        "repair": "repair service",
        "recycle": "recyclers",
        "collective": "scrap collection",
        "industrial_symbiosis": "material processors",
        "upcycle": "upcycling workshop",
        "compost": "composting facility",
        "professional": "authorized waste handler"
    }

    purpose = purposes.get(category)
    return f"{material} {purpose}" if purpose else None



def maps_search_links(material, category, pin, locality):
    from urllib.parse import urlencode

    if not pin:
        return []

    if not re.fullmatch(r"[\w][\w -]{1,75}", material):
        return []

    terms = map_search_terms(material, category)

    if not terms:
        return []

    geography = geographic_context(pin)

    areas = [
        ("Search PIN area", geography["local"]),
        ("Search wider district", geography["regional"])
    ]

    return [
        {
            "label": label,
            "url": "https://www.google.com/maps/search/?" +
                   urlencode({
                       "api": 1,
                       "query": f"{terms} {area}"
                   })
        }
        for label, area in areas
    ]




def places_inventory(pin, items):
    """Optional billed API. Search only explicitly authorized public discovery."""
    import os
    import httpx
    from core.waste_intelligence import restricted_material

    if os.getenv("REGEN_ENV") == "test" or os.getenv("REGEN_GOOGLE_PLACES_ENABLED") != "1":
        return {"status": "disabled", "places_services": []}
    key = os.getenv("REGEN_GOOGLE_PLACES_API_KEY")
    if not key:
        return {"status": "unavailable", "places_services": []}
    queries = []
    for item in items:
        if (not re.fullmatch(r"[A-Za-z][A-Za-z -]{2,54}", item.material)
                or item.contaminated or item.condition.casefold() in {"contaminated", "spoiled"}):
            continue
        category = "professional" if restricted_material(item.material, {}) else (
            "repair" if item.condition.casefold() == "damaged" else "recycle")
        queries.append((item.material, category))
    matches = []
    statuses = []
    for material, category in list(dict.fromkeys(queries))[:2]:
        def lookup():
            try:
                check_research_deadline()
                with httpx.Client(timeout=research_timeout(), trust_env=False, follow_redirects=False) as client:
                    with client.stream("POST", "https://places.googleapis.com/v1/places:searchText",
                        headers={"X-Goog-Api-Key":key, "X-Goog-FieldMask":
                                 "places.displayName,places.formattedAddress,places.googleMapsUri,places.businessStatus"},
                        json={"textQuery":f"{material} {map_search_terms(material, category)} {pin} India",
                              "regionCode":"IN","pageSize":5}) as response:
                        response.raise_for_status()
                        content = bytearray()
                        for block in response.iter_bytes():
                            check_research_deadline()
                            content.extend(block)
                            if len(content) > 500_000:
                                raise ValueError("Places response exceeded size limit.")
                    entries = json.loads(content).get("places", [])
                    entries = entries[:5] if isinstance(entries, list) else []
            except (httpx.HTTPError, ValueError, TypeError, AttributeError):
                return {"status":"unavailable","services":[]}
            rows = []
            for entry in entries:
                if not isinstance(entry, dict) or not isinstance(entry.get("displayName"), dict):
                    continue
                label = entry["displayName"].get("text", "")
                address = entry.get("formattedAddress", "")
                source = entry.get("googleMapsUri", "")
                try:
                    place_url = urlsplit(source)
                except (ValueError, TypeError):
                    continue
                if (entry.get("businessStatus") != "OPERATIONAL" or not isinstance(label, str) or not label or not isinstance(address, str)
                        or not re.search(rf"(?<!\d){pin}(?!\d)", address)
                        or place_url.scheme != "https" or place_url.username or place_url.password
                        or place_url.hostname not in {"maps.google.com", "www.google.com"}
                        or not relevant_listing({"material":material}, category, {"organization":label})):
                    continue
                rows.append({"organization":label,"material":material,"pathways":[category],"service_pins":[pin],
                             "coverage_basis":"published_location","source_url":source,
                             "description":"Google Maps lists a matching business name at this PIN. Confirm acceptance and transfer terms.",
                             "evidence_type":"google_places"})
            return {"status":"found" if rows else "no_results","services":rows}
        # Places content is used for this response. Retention is subject to Google Maps terms.
        result = lookup()
        statuses.append(result["status"])
        matches.extend({**row, "provenance":"live_research"} for row in result["services"])
    return {"status": "found" if matches else "unavailable" if "unavailable" in statuses else "no_results",
            "places_services": matches}


def inventory_discovery(pin, items):
    if not pin:
        return {"status": "pin_not_provided", "services": []}
    return places_inventory(pin, items)


def research_service_leads(item, pin, category, rows):
    for row in rows:
        paths, aliases = row.get("pathways"), row.get("aliases", [])
        if not isinstance(paths, list) or category not in paths or not isinstance(aliases, list):
            continue
        if not {normalize(item["material"]), normalize(item.get("original_material"))} & {
                normalize(name) for name in [row.get("material"), *aliases] if name}:
            continue
        name, source, description = (row.get(key) for key in ("organization", "source_url", "description"))
        if not all(isinstance(value, str) and 0 < len(value) <= 450 for value in (name, source, description)):
            continue
        try:
            url = urlsplit(source)
            if url.scheme != "https" or not url.hostname or url.username or url.password:
                continue
        except ValueError:
            continue
        pins = row.get("service_pins")
        remote = (row.get("coverage_basis") == "remote_coverage"
                  and row.get("transfer") in {"shipping", "collection"}
                  and row.get("transfer_documented") is True)
        if not isinstance(pins, list) or (pin not in pins and
                row.get("coverage_basis") not in {
                    "locality_mentioned", "district_mentioned"
                } and not remote):
            continue
        conditions = row.get("conditions")
        if conditions is not None and (not isinstance(conditions, list) or
                normalize(item["condition"]) not in {normalize(condition) for condition in conditions}):
            continue
        minimum, maximum = row.get("minimum_quantity"), row.get("maximum_quantity")
        bounded = minimum is not None or maximum is not None
        quantity = convert_quantity(item["quantity"], item["unit"], row.get("unit")) if bounded else None
        if bounded and (quantity is None or minimum is not None and
                (number(minimum) is None or quantity < number(minimum)) or maximum is not None and
                (number(maximum) is None or quantity > number(maximum))):
            continue
        yield {"organization": name, "source_url": source, "description": description,
               "source": "Published organization evidence", "provenance": row["provenance"],
               "locality": row.get("locality") if isinstance(row.get("locality"), str) else None,
               "coverage": row.get("coverage_basis", "published_pin"),
               "collection_documented": row.get("transfer_documented") is True,
               "evidence_type": row.get("evidence_type"),
                "publisher_evidence": row.get("publisher_evidence"),
                "publisher_title": row.get("publisher_title"),
                "quantity_documented": bounded, "condition_documented": bool(conditions),
               "verification": "public_unverified", "acceptance_confirmed": False}


def service_priority(lead):
    distance = lead.get("distance_km")
    coverage = {
        "published_pin": 5,
        "published_location": 4,
        "reviewed_pin_reference": 4,
        "documented_region": 3,
        "locality_mentioned": 3,
        "district_mentioned": 2,
        "remote_coverage": 1
    }
    return (lead.get("acceptance_confirmed") is True, coverage.get(lead.get("coverage"), 0),
            bool(lead.get("condition_documented")), bool(lead.get("quantity_documented")),
            bool(lead.get("collection_documented")),
            lead.get("net_paise") if isinstance(lead.get("net_paise"), (int, float)) else float("-inf"),
            -(distance if isinstance(distance, (int, float)) else float("inf")))



def final_service_compatible(item, lead, category=None):
    """Validate business activity independently of material identity."""

    name = normalize(lead.get("organization"))
    description = normalize(lead.get("description"))
    text = name + " " + description

    if not name or len(name) < 3:
        return False

    if re.match(
        r"^(how to|what is|benefits of|guide to|why )",
        name
    ):
        return False

    # These describe business activities, not individual materials.

    procurement = bool(re.search(
        r"\b(buyer|buyers|buyback|buying|buys|purchase|"
        r"purchases|purchasing|procurement|we buy|"
        r"we collect|collection|collects|accepts|"
        r"acceptance|scrap dealer|scrap dealers)\b",
        text
    ))

    supplier = bool(re.search(
        r"\b(supplier|suppliers|exporter|exporters|"
        r"wholesaler|wholesale|retailer|retail|"
        r"manufacturer|manufacturers|shop online|"
        r"add to cart|selling price|product catalogue)\b",
        text
    ))

    donation = bool(re.search(
        r"\b(accepts donations|donation collection|"
        r"donated goods|accepts used|collects donated|"
        r"in-kind donations|donation centre)\b",
        text
    ))

    recycling = bool(re.search(
        r"\b(recycling|recycler|recyclers|"
        r"material recovery|waste collection|"
        r"scrap collection|scrap dealer)\b",
        text
    ))

    repair = bool(re.search(
        r"\b(repair|repairs|repairing|"
        r"refurbishment|refurbishing)\b",
        text
    ))

    if supplier and not re.search(
        r"\b(buys|buys from|buys back|we buy|we purchase|purchases from|"
        r"buyback|procurement|we collect|collects|accepts)\b", text
    ):
        return False

    if category == "sell":
        return procurement

    if category == "donate":
        return donation

    if category in {"recycle", "collective"}:
        return recycling or procurement

    if category == "repair":
        return repair

    if category == "industrial_symbiosis":
        return procurement

    if category == "professional":
        return bool(lead.get("acceptance_confirmed"))

    return procurement or recycling or donation or repair





def attach_local_discovery(item, intelligence, pin, result):
    pathways = intelligence.get("pathways", [])

    for route in pathways:
        route["public_services"] = []
        route["discovery_status"] = (
            "pending" if pin else "pin_not_provided"
        )

    if not pin or not pathways:
        return intelligence

    if item.get("contaminated"):
        for route in pathways:
            route["discovery_status"] = "authorized_service_required"
        return intelligence

    services = result.get("services", [])

    for route in pathways:
        category = route.get("service_pathway", route["category"])
        if not category:
            continue

        allowed = CATEGORY_MAP.get(
            category, set()
        )

        reviewed = published_service_leads(item, pin, category)
        matches = list(research_service_leads(item, pin, category, [*result.get("research_services", []), *result.get("places_services", [])]))

        for service in services:
            if category == "professional" or service.get("category") not in allowed or not relevant_listing(item, category, service):
                continue

            matches.append({
                **service,
                "acceptance_confirmed": False,
                "provenance": "cached_research" if result.get("cache_hit") else "live_research",
                "coverage": "near_postal_centroid",
                "relevance": "published_material_signal",
                "notice": (
                    "Public listing. Material acceptance, "
                    "pricing and pickup require confirmation."
                ),
            })

        verified = [{**service, "acceptance_confirmed":True, "coverage":"published_pin",
                     "condition_documented":True, "quantity_documented":True,
                     "collection_documented":service.get("transfer") == "pickup"}
                    for service in route.get("verified_services", [])]
        matches = [
            lead for lead in matches
            if final_service_compatible(item, lead, category)
        ]

        ranked = sorted(
            [*verified, *reviewed, *matches],
            key=service_priority,
            reverse=True
        )
        unique = {}
        for lead in ranked:
            unique.setdefault(normalize(lead["organization"]), lead)
        displayed = list(unique.values())[:5]
        route["verified_services"] = [lead for lead in displayed if lead.get("acceptance_confirmed") is True]
        route["public_services"] = [lead for lead in displayed if lead.get("acceptance_confirmed") is not True]

        route["discovery_status"] = (
            "public_leads_found" if route["public_services"] else result.get("status", "no_compatible_evidence")
        )

    intelligence["local_discovery"] = {
        "status": result.get("status"),
        "material_research_status": result.get("material_research_status"),
        "general_research_status": result.get("general_research_status"),
        "general_search_metadata": result.get("general_search_metadata"),
        "locality": result.get("locality"),
        "source": "Reviewed organization references and optional public research",
        "attribution": result.get("attribution"),
        "public_lead_count": len({normalize(s["organization"]) for route in pathways for s in route["public_services"]}),
        "verified_acceptance": False,
    }

    intelligence.setdefault("events", []).append({
        "action": "public_service_discovery",
        "completed": result.get("status") != "pending",
        "status": result.get("status"),
        "public_lead_count": len({normalize(s["organization"]) for route in pathways for s in route["public_services"]}),
    })

    return intelligence
