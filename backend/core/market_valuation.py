"""Evidence-based recovery valuation."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date
from urllib.parse import urlparse

MASS_FACTORS = {
    "g": Decimal("0.001"),
    "kg": Decimal("1"),
    "tonnes": Decimal("1000"),
}


def number(value):
    try:
        result = Decimal(str(value))
        if result.is_finite() and 0 <= result <= Decimal("1000000000000"):
            return result
    except (InvalidOperation, ValueError, TypeError):
        pass
    return None


def convert_quantity(quantity, source_unit, target_unit):
    quantity = number(quantity)

    if quantity is None or quantity <= 0:
        return None

    if source_unit == target_unit:
        return quantity

    if source_unit in MASS_FACTORS and target_unit in MASS_FACTORS:
        return (
            quantity * MASS_FACTORS[source_unit]
            / MASS_FACTORS[target_unit]
        )

    return None



def quantity_range(item, evidence):
    target = evidence.get("unit")
    direct = convert_quantity(
        item.get("quantity"), item.get("unit"), target
    )
    if direct is not None:
        return direct, direct

    count = number(item.get("quantity"))
    if item.get("unit") != "pcs" or count is None or count <= 0:
        return None

    # Unit mass must come from documented compatible evidence.
    if evidence.get("reviewed") is not True:
        return None

    if not evidence.get("unit_mass_source_url", "").startswith("https://"):
        return None

    low = number(evidence.get("unit_mass_min_g"))
    high = number(evidence.get("unit_mass_max_g"))

    if low is None or high is None or not 0 < low <= high:
        return None

    minimum = convert_quantity(count * low, "g", target)
    maximum = convert_quantity(count * high, "g", target)

    if minimum is None or maximum is None:
        return None

    return minimum, maximum


def money(value):
    return float(
        value.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
    )


def unavailable(reason):
    return {
        "status": "insufficient_evidence",
        "minimum_inr": None,
        "maximum_inr": None,
        "net_minimum_inr": None,
        "net_maximum_inr": None,
        "reason": reason,
    }


def value_pathway(item, pathway, evidence=None):
    category = pathway.get("category", "")

    if category == "donate":
        return {
            "status": "non_commercial",
            "minimum_inr": 0,
            "maximum_inr": 0,
            "value_type": "direct_cash_return",
            "reason": "Donation does not generate sale income.",
        }

    if not evidence:
        if pathway.get("quote_basis"):
            return {**unavailable(pathway["quote_basis"]), "clarification": pathway["quote_basis"]}
        details = {
            "sell": "Record the exact model, title or grade and get a condition-based purchase quote.",
            "repair": "Get a repair-cost quote separately from any post-repair buyback offer.",
            "reuse": "Use a comparable replacement cost only if the item will replace a planned purchase.",
            "recycle": "Confirm the accepted grade, eligible weight and current rate. Piece counts cannot establish a weight-based value.",
            "upcycle": "Estimate the saleable output and its price, then document production and selling costs.",
            "professional": "Ask a qualified handler whether they accept this material and what treatment and transport cost.",
            "compost": "Confirm accepted moisture and contamination limits and ask for collection and processing charges.",
            "industrial_symbiosis": "Request feedstock grade, minimum lot, delivery costs and a processor offer for the eligible quantity.",
            "collective": "Confirm combined eligible weight, the collector’s minimum and all collection charges.",
        }
        reason = details.get(category, "Document grade, eligible quantity and transfer requirements, then request an itemized quote from an accepting provider.")
        material = item.get("material", "").casefold()
        if category in {"sell", "repair"}:
            if any(label in material for label in ("phone", "mobile", "laptop")):
                reason = "What is the model and visible fault? A condition-based quote needs both."
            elif category == "sell" and "book" in material:
                reason = "What are the titles and editions, and are the copies intact?"
        return {**unavailable(reason), "clarification": reason}

    source = str(evidence.get("source_url", ""))
    try:
        parsed = urlparse(source)
    except ValueError:
        return unavailable("Missing valid evidence source.")

    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return unavailable("Missing valid evidence source.")

    try:
        observed = date.fromisoformat(
            str(evidence["observed_on"])
        )
    except (KeyError, ValueError, TypeError):
        return unavailable("Missing evidence date.")

    age = (date.today() - observed).days

    if age < 0:
        return unavailable("Invalid evidence date.")

    if evidence.get("reviewed") is not True:
        return unavailable("Market evidence requires review.")

    if evidence.get("category") != category:
        return unavailable("Evidence does not match the pathway.")

    material = str(item.get("material", "")).strip().casefold()
    evidence_material = str(
        evidence.get("material", "")
    ).strip().casefold()

    if not material or material != evidence_material:
        return unavailable("Material compatibility not established.")

    if evidence.get("condition") != item.get("condition"):
        return unavailable("Condition compatibility not established.")

    quantities = quantity_range(item, evidence)

    if quantities is None:
        low = number(evidence.get("rate_min_inr"))
        high = number(evidence.get("rate_max_inr"))

        if low is None or high is None or high < low:
            return unavailable("Invalid market rate.")

        if evidence.get("value_type", "gross_reference") != "gross_reference":
            return unavailable("Compatible quantity required.")

        return {
            **unavailable(
                "Multiply eligible measured weight by the published rate."
            ),
            "status": "rate_only",
            "rate_min_inr": money(low),
            "rate_max_inr": money(high),
            "unit": evidence["unit"],
            "source_url": source,
            "observed_on": observed.isoformat(),
            "locality": evidence.get("locality"),
            "scope": evidence.get("scope"),
            "value_type": "gross_reference",
            "applicability": evidence.get("applicability"),
            "clarification": "Measure eligible dry weight to calculate total recovery value."
        }

    quantity_low, quantity_high = quantities
    quantity = quantity_low

    low = number(evidence.get("rate_min_inr"))
    high = number(evidence.get("rate_max_inr"))

    if low is None or high is None or high < low:
        return unavailable("Invalid market rate range.")

    gross_low = quantity_low * low
    gross_high = quantity_high * high

    costs = number(evidence.get("costs_inr"))

    value_type = evidence.get("value_type", "gross_reference")
    if value_type not in {"gross_reference", "avoided_purchase", "treatment_cost", "refurbishment_cost", "output_revenue"}:
        return unavailable("Unrecognized financial basis.")
    cost_only = value_type in {"treatment_cost", "refurbishment_cost"}
    if value_type == "output_revenue":
        yield_ratio = number(evidence.get("saleable_output_per_input_unit"))
        if category not in {"repair", "upcycle"} or yield_ratio is None or not evidence.get("output_unit"):
            return unavailable("A documented saleable output yield is required.")
        gross_low *= yield_ratio
        gross_high *= yield_ratio
    low_net = -gross_high if cost_only else gross_low - costs if costs is not None else None
    high_net = -gross_low if cost_only else gross_high - costs if costs is not None else None
    return {
        "status": "estimated",
        "minimum_inr": money(gross_low),
        "maximum_inr": money(gross_high),
        "net_minimum_inr": money(low_net) if low_net is not None else None,
        "net_maximum_inr": money(high_net) if high_net is not None else None,
        "financial_basis": "cost" if cost_only else "avoided_expenditure" if value_type == "avoided_purchase" else "revenue",
        "output_unit": evidence.get("output_unit"),
        "saleable_output_per_input_unit": evidence.get("saleable_output_per_input_unit"),
        "rate_min_inr": money(low),
        "rate_max_inr": money(high),
        "quantity": float(quantity) if quantity_low == quantity_high else None,
        "quantity_min": float(quantity_low),
        "quantity_max": float(quantity_high),
        "quantity_estimated": item.get("unit") == "pcs" and evidence.get("unit") != "pcs",
        "unit_mass_source_url": evidence.get("unit_mass_source_url"),
        "costs_inr": money(costs) if costs is not None else None,
        "unit": evidence["unit"],
        "value_type": value_type,
        "source_url": source,
        "observed_on": observed.isoformat(),
        "locality": evidence.get("locality"),
        "scope": evidence.get("scope"),
        "applicability": evidence.get("applicability"),
        "evidence_type": evidence.get("evidence_type"),
        "service_pins": evidence.get("service_pins", []),
        "freshness": (
            "recent_reference"
            if age <= 30 else "historical_reference"
        ),
        "reason": (
            "Reference-based estimate; "
            "not a guaranteed transaction."
        ),
    }

def enrich_pathways(item, intelligence, services):
    """Attach financial evidence to each recovery alternative."""

    category_mapping = {
        "industrial_symbiosis": {"industrial_symbiosis"},
        "sell": {"sell", "resale", "buyback"},
        "recycle": {"recycle", "recycling"},
        "reuse": {"reuse", "direct_reuse", "internal_redistribution"},
        "repair": {"repair", "refurbishment"},
        "upcycle": {"upcycle", "upcycling"},
        "collective": {"collective", "collective_recovery"},
        "professional": {"authorized_disposal", "professional"},
        "compost": {"compost", "composting"},
        "donate": {"donate", "donation"},
    }

    for route in intelligence.get("pathways", []):
        category = route.get("category", "")
        allowed = category_mapping.get(route.get("service_pathway", category), set())

        matches = [
            service for service in services
            if service.get("pathway") in allowed
        ]

        route["verified_services"] = matches
        route["valuation"] = value_pathway(item, route)

        if category == "donate":
            continue

        if category == "reuse":
            savings = [
                number(service.get("avoided_purchase_paise"))
                for service in matches
            ]

            savings = [
                value for value in savings
                if value is not None and value > 0
            ]

            if savings:
                route["valuation"] = {
                    "status": "estimated",
                    "minimum_inr": money(min(savings) / 100),
                    "maximum_inr": money(max(savings) / 100),
                    "value_type": "avoided_purchase",
                    "reason": (
                        "Potential avoided expenditure, "
                        "not cash income."
                    ),
                }

            continue

        mass = convert_quantity(
            item.get("quantity"),
            item.get("unit"),
            "kg",
        )

        gross_values = []
        net_values = []

        for service in matches:
            rate = number(
                service.get("quote_paise_per_kg")
            )

            if rate is not None and mass is not None:
                gross_values.append(mass * rate / 100)

            try:
                net = Decimal(str(service.get("net_paise")))

                if net.is_finite():
                    net_values.append(net / 100)

            except (InvalidOperation, ValueError, TypeError):
                pass

        if gross_values:
            route["valuation"] = {
                "status": "estimated",
                "minimum_inr": money(min(gross_values)),
                "maximum_inr": money(max(gross_values)),
                "net_minimum_inr": (
                    money(min(net_values))
                    if net_values else None
                ),
                "net_maximum_inr": (
                    money(max(net_values))
                    if net_values else None
                ),
                "value_type": "gross_service_quote",
                "provenance": "verified_quotation",
                "reason": (
                    "Based on eligible service quotations. "
                    "Final acceptance is not guaranteed."
                ),
            }

        elif net_values:
            route["valuation"] = {
                "status": "estimated",
                "minimum_inr": money(min(net_values)),
                "maximum_inr": money(max(net_values)),
                "value_type": "net_service_quote",
                "provenance": "verified_quotation",
                "reason": "Projected net service value.",
            }

    return intelligence

