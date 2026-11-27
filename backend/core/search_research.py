"""Bounded public search. Search-hit URLs are citations and never fetch targets."""

import json
import os
import re
import time
from threading import Lock
from datetime import date
from contextvars import copy_context
from html import unescape
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, ConfigDict, Field

from core.market_evidence import normalize, research_result
from core.public_discovery import cached, check_research_deadline, research_remaining, research_timeout

INTENTS = {
    "collective": ("scrap collection", "bulk collection", "pickup", "collects"),
    "industrial_symbiosis": ("procurement", "feedstock", "purchases", "buyer"),
    "sell": ("buyback", "buys", "buying", "purchase", "procurement", "buyer", "buyers"),
    "reuse": ("reuse", "exchange", "redistribution"),
    "upcycle": ("upcycling", "repurposing"),
    "repair": ("repair", "refurbish", "refurbishment"),
    "recycle": ("recycling", "recycler", "recycles"),
    "compost": ("composting", "compost facility"),
    "donate": ("donation", "accepts donations", "donate"),
    "professional": ("recycling", "recycle", "registered recycler"),
}
LABEL = re.compile(r"^[A-Za-z][A-Za-z -]{2,54}$")
PRIVATE_WORDS = {"password", "secret", "credential", "address", "ignore", "instruction", "system",
                 "prompt", "token", "account", "aadhar", "aadhaar"}


_mwmbl_lock = Lock()
_mwmbl_next_request = 0.0
_provider_cooldown = {}


class SourceCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: int = Field(ge=0, le=7)
    organization: str = Field(min_length=3, max_length=100)
    evidence: str = Field(min_length=12, max_length=400)


class CandidateEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    leads: list[SourceCandidate] = Field(max_length=5)


def source_url(value):
    if not isinstance(value, str) or len(value) > 500 or any(char.isspace() for char in value):
        return None
    try:
        address = urlsplit(value)
        hostname = address.hostname or ""
        if (address.scheme != "https" or address.username or address.password or address.port not in (None, 443)
                or not re.fullmatch(r"(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,24}", hostname)
                or hostname.endswith((".localhost", ".local", ".internal", ".test", ".onion"))):
            return None
        return address._replace(fragment="", query="").geturl()
    except ValueError:
        return None


def searx_url(value):
    try:
        url = urlsplit(value)
        if (url.scheme == "http" and url.hostname == "127.0.0.1" and url.port
                and url.path == "/search" and not (url.username or url.password or url.query or url.fragment)):
            return value
    except ValueError:
        pass
    raise ValueError("SearXNG needs an explicit loopback /search URL.")


def search_provider(mode):
    if mode == "mwmbl":
        return mode, "https://api.mwmbl.org/api/v2/search/"
    if mode == "searxng":
        return mode, searx_url(os.getenv("REGEN_SEARXNG_URL", ""))
    if mode == "brave" and os.getenv("REGEN_BRAVE_API_KEY"):
        return mode, "https://api.search.brave.com/res/v1/web/search"
    if mode == "tavily" and os.getenv("REGEN_TAVILY_API_KEY"):
        return mode, "https://api.tavily.com/search"
    return None


def configured_providers():
    modes = os.getenv("REGEN_SEARCH_PROVIDERS") or os.getenv("REGEN_SEARCH_PROVIDER", "")
    eligible = []
    for name in dict.fromkeys(mode.strip().casefold() for mode in modes.split(",")):
        try:
            provider = search_provider(name)
        except ValueError:
            continue
        if provider:
            eligible.append(provider)
    return eligible


def clean_excerpt(value):
    if not isinstance(value, str):
        return ""
    content = unescape(re.sub(r"<[^>]*>", " ", value[:3500]))
    content = re.sub(r"\S+@\S+|(?:\+?91[ -]?)?[6-9]\d{9}", "[redacted]", content)
    return " ".join(content.split())


def search_hits(provider, query):
    mode, url = provider
    with _mwmbl_lock:
        if _provider_cooldown.get(mode, 0) > time.monotonic():
            raise ValueError("Search provider temporarily paused.")
    headers = {"Accept": "application/json"}
    params = {"q": query, "format": "json", "categories": "general", "safesearch": 2}
    body = None
    if mode == "mwmbl":
        params = {"q": query}
    if mode == "brave":
        headers["X-Subscription-Token"] = os.environ["REGEN_BRAVE_API_KEY"]
        params = {"q": query, "count": 8, "country": "IN", "safesearch": "strict"}
    elif mode == "tavily":
        headers["Authorization"] = "Bearer " + os.environ["REGEN_TAVILY_API_KEY"]
        params = None
        body = {"query": query, "max_results": 8, "search_depth": "basic",
                "include_raw_content": False, "include_answer": False, "safe_search": True}
    if mode == "mwmbl":
        global _mwmbl_next_request
        with _mwmbl_lock:
            now = time.monotonic()
            scheduled = max(now, _mwmbl_next_request)
            delay = scheduled - now
            if delay >= research_remaining():
                raise httpx.TimeoutException("Search rate limit exceeds research budget.")
            _mwmbl_next_request = scheduled + 1.1
        time.sleep(delay)
    with httpx.Client(timeout=research_timeout(), trust_env=False, follow_redirects=False) as client:
        with client.stream("POST" if body else "GET", url, params=params, json=body, headers=headers) as response:
            if response.status_code == 429:
                wait = response.headers.get("Retry-After", "")
                seconds = max(60, int(wait)) if wait.isascii() and wait.isdigit() and len(wait) <= 10 else 300
                with _mwmbl_lock:
                    _provider_cooldown[mode] = time.monotonic() + seconds
            response.raise_for_status()
            content = bytearray()
            for chunk in response.iter_bytes():
                check_research_deadline()
                content.extend(chunk)
                if len(content) > 500_000:
                    raise ValueError("Search result exceeded size limit.")
    data = json.loads(content)
    if mode == "mwmbl" and isinstance(data, list):
        data = {"results": data}

    if not isinstance(data, dict):
        raise ValueError("Invalid search response.")
    if mode == "brave":
        data = data.get("web") or {}
    rows = data.get("results", [])
    if not isinstance(rows, list):
        raise ValueError("Invalid search results.")
    hits = []
    for row in rows[:8]:
        if not isinstance(row, dict):
            continue
        url = source_url(row.get("url"))
        excerpt = clean_excerpt(row.get("description") or row.get("content") or row.get("extract") or row.get("snippet"))[:700]
        title = clean_excerpt(row.get("title"))[:140]
        if url and title and excerpt:
            hits.append({"url": url, "title": title, "excerpt": excerpt})
    return hits


def words(label):
    values = set(re.findall(r"[a-z]{3,}", re.sub(r"\be[ -]waste\b", "ewaste", normalize(label))))
    return {value.removesuffix("s") for value in values - {"old", "used", "broken", "damaged", "waste", "scrap"}}


def compatible_material(label, text):
    target = words(label)
    return bool(target and target <= words(text))



def service_evidence_compatible(material, title, excerpt):
    text = f"{title} {excerpt}".casefold()

    if re.search(
        r"^(what is|how to|why |top \d+|guide to|benefits of)",
        title.strip(), re.I
    ):
        return False


    if re.search(r"\b(hair|keratin)\b", material, re.I):
        return bool(
            re.search(
                r"\b(human hair|salon hair|hair waste|hair cuttings|keratin)\b",
                text
            )
            and re.search(
                r"\b(we buy|we purchase|we collect|we accept|"
                r"procurement of|purchase from|collects hair|"
                r"accepts hair waste)\b",
                text
            )
            and not re.search(
                r"\b(retail|shop now|add to cart|"
                r"buy online|hair extensions|selling price)\b",
                text
            )
        )

    if re.search(r"\b(cans?|plastic bottles?|pet bottles?)\b", material, re.I):
        return bool(
            compatible_material(material, text)
            and re.search(r"\b(scrap|kabadiwala|kabadi|recycling|waste)\b", text)
            and re.search(r"\b(buy|buys|buyer|buying|purchase|pickup|collection|collects)\b", text)
        )

    return compatible_material(material, excerpt)


def candidate_leads(material, pin, intent, hits, proposal):
    proposed = {candidate.source: candidate for candidate in proposal.leads} if proposal else {}
    leads = []
    for index, hit in enumerate(hits):
        excerpt = hit["excerpt"]

        if not service_evidence_compatible(
            material, hit["title"], excerpt
        ):
            continue

        if (not compatible_material(material, excerpt) or
                not any(re.search(rf"\b{term}\b", hit["title"] + " " + excerpt, re.I) for term in INTENTS[intent])):
            continue
        candidate = proposed.get(index)
        if (candidate and candidate.evidence in excerpt
                and candidate.organization.casefold() in hit["title"].casefold()):
            name = candidate.organization
        else:
            segments = re.split(r"\s+[|–—]\s+|\s+-\s+", hit["title"])
            brand = (urlsplit(hit["url"]).hostname or "").removeprefix("www.").split(".")[0]
            name = next((segment for segment in segments if normalize(segment).replace(" ", "") == brand), segments[0])
        if (not 3 <= len(name) <= 100 or not any(part not in words(material) for part in words(name))
                or not re.fullmatch(r"[\w .,&()'’+-]+", name)):
            continue
        coverage = geographic_evidence(
            pin, hit["title"] + " " + excerpt
        )

        if not coverage:
            continue

        leads.append({
            "organization": name,
            "source_url": hit["url"],
            "material": material,
            "pathways": [intent],
            "service_pins": [pin] if coverage == "published_location" else [],
            "coverage_basis": coverage,
            "description": excerpt[:400],
            "publisher_evidence": excerpt[:700],
            "publisher_title": hit["title"],
            "evidence_type": "indexed_public_excerpt"
        })
    return leads



def published_benchmark_rates(material, condition, pin, intent, hits):
    if intent not in {"sell", "recycle"}:
        return []

    allowed = {
        host.strip().lower()
        for host in os.getenv("REGEN_SEARCH_RATE_HOSTS", "").split(",")
        if host.strip()
    }

    rows = []

    for hit in hits:
        host = urlsplit(hit["url"]).hostname or ""

        if host not in allowed:
            continue

        excerpt = hit["excerpt"]
        lower = excerpt.casefold()

        if not compatible_material(material, excerpt):
            continue

        if re.search(
            r"\b(retail|mrp|selling price|starting from|up to|wholesale selling)\b",
            lower
        ):
            continue

        dates = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", excerpt)

        if len(set(dates)) != 1:
            continue

        observed = dates[0]

        try:
            age = (date.today() - date.fromisoformat(observed)).days
        except ValueError:
            continue

        if not 0 <= age <= 365:
            continue

        # Require a purchase-rate statement explicitly associated
        # with the material and its condition.
        for segment in re.split(r"[;\n|]", excerpt):
            if not compatible_material(material, segment):
                continue

            if not re.search(
                r"\b(buying rate|purchase rate|buyback rate|"
                r"procurement price|we buy)\b",
                segment, re.I
            ):
                continue

            if not re.search(
                r"\b" + re.escape(condition) + r"\b",
                segment, re.I
            ):
                continue

            matches = list(re.finditer(
                r"(?:\u20b9|INR|Rs\.?)\s*"
                r"(\d{1,6}(?:\.\d{1,2})?)"
                r"(?:\s*(?:-|\u2013|to)\s*"
                r"(?:\u20b9|INR|Rs\.?)?\s*"
                r"(\d{1,6}(?:\.\d{1,2})?))?"
                r"\s*(?:/|per)\s*"
                r"(kg|kilogram|pcs|piece|pieces|litre|liter)\b",
                segment, re.I
            ))

            if len(matches) != 1:
                continue

            low, high, unit = matches[0].groups()
            high = high or low

            if not 0 < float(low) <= float(high):
                continue

            unit = {
                "kilogram": "kg",
                "piece": "pcs",
                "pieces": "pcs",
                "litre": "L",
                "liter": "L"
            }.get(unit.lower(), unit.lower())

            published_pins = set(
                re.findall(r"\b[1-9]\d{5}\b", excerpt)
            )

            local = bool(pin and published_pins == {pin})

            national = (
                not published_pins
                and bool(re.search(
                    r"\b(all india|pan.india|nationwide|"
                    r"national benchmark|india.wide)\b",
                    lower
                ))
            )

            if not local and not national:
                continue

            rows.append({
                "material": material,
                "condition": condition,
                "category": intent,
                "unit": unit,
                "reviewed": True,
                "service_pins": [pin] if local else [],
                "scope": "India" if national else "local",
                "observed_on": observed,
                "source_url": hit["url"],
                "rate_min_inr": low,
                "rate_max_inr": high,
                "value_type": "gross_reference",
                "evidence_type": "indexed_published_buying_rate",
                "applicability": (
                    "Published purchase-rate benchmark; "
                    "actual acceptance and costs require confirmation."
                )
            })

    return rows


def indexed_rates(material, condition, pin, intent, hits):
    # Operator-reviewed domains may publish dated tables as publisher-supplied excerpts.
    allowed = {host.strip().lower() for host in os.getenv("REGEN_SEARCH_RATE_HOSTS", "").split(",") if host.strip()}
    if intent not in {"sell", "recycle"} or condition not in {"dry", "used", "good"} or not pin:
        return []
    rows = []
    for hit in hits:
        text = hit["excerpt"]
        if urlsplit(hit["url"]).hostname not in allowed or any(term in text.casefold() for term in ("starting", "up to", "asking", "retail")):
            continue
        match = re.search(r"\b(\d{4}-\d{2}-\d{2})\s*[·|;]\s*([A-Za-z -]{3,70})\s*[·|;]\s*"
                          r"(dry|used|good)\s*[·|;]\s*(?:buying rate|purchase rate)\s*[: ]+"
                          r"(?:₹|INR\s*)(\d{1,6}(?:\.\d{1,2})?)\s*/\s*(kg|pcs|L)\s*[·|;]\s*(\d{6})\b", text, re.I)
        if not match:
            continue
        observed, label, grade, rate, unit, published_pin = match.groups()
        if not compatible_material(material, label) or grade.casefold() != condition or pin != published_pin:
            continue
        try:
            age = (date.today() - date.fromisoformat(observed)).days
        except ValueError:
            continue
        if 0 <= age <= 90:
            rows.append(dict(material=material, condition=condition, category=intent, unit=unit, reviewed=True,
                service_pins=[pin], observed_on=observed, source_url=hit["url"], rate_min_inr=rate, rate_max_inr=rate,
                evidence_type="indexed_published_buying_rate", applicability="Indexed published buying rate. Confirm acceptance and total costs."))
    return rows


def distinct_rows(rows, *fields):
    unique = {}
    for row in rows:
        key = tuple(normalize(row.get(field)) for field in fields)
        unique.setdefault(key, row)
    return list(unique.values())


def search_query(provider, material, intent, pin, alternative, locality=None):
    from core.recovery_discovery import map_search_terms

    terms = map_search_terms(material, intent) or material

    from core.postal_intelligence import geographic_context

    geography = geographic_context(pin)
    area = "India" if alternative else re.sub(r",?\s*India(?=\s|$)", "", geography["local"]).strip()

    if intent == "donate":
        terms = f"{material} accepts donations"

    return f"{terms} {area}"



def general_research(items, pin, planned_rows):
    if os.getenv("REGEN_ENV") == "test":
        return {"status": "offline", "rows": [], "services": []}
    providers = configured_providers()
    if not providers:
        return {"status": "search_provider_not_configured", "rows": [], "services": []}

    locality = None
    for result in planned_rows:
        postal = result.get("postal_locality")
        if isinstance(postal, dict):
            name = postal.get("name", "")
            if isinstance(name, str) and re.fullmatch(
                r"[A-Za-z0-9 ,.-]{2,120}", name
            ):
                locality = name
                break

    tasks = {}
    for item, result in zip(items, planned_rows):
        routes = result["intelligence"]["pathways"]
        documented = {normalize(lead["organization"]) for route in routes for lead in route.get("public_services", [])}
        if len(documented) >= 2 or any(route.get("verified_services") for route in routes):
            continue
        tokens = words(item.material)
        if not LABEL.fullmatch(item.material) or not tokens or tokens & PRIVATE_WORDS:
            continue
        paths = [route["category"] for route in routes if route["category"] in INTENTS and not route.get("conditional_completion")]
        if paths:
            key = normalize(item.material), normalize(item.condition)
            current = tasks.get(key, [])
            tasks[key] = list(dict.fromkeys([*current, *paths]))[:3]
    tasks = list(tasks.items())[:20]
    if not tasks:
        return {"status": "no_searchable_materials", "rows": [], "services": []}

    from concurrent.futures import ThreadPoolExecutor

    query_locks = {}
    query_guard = Lock()
    request_ms = []
    remaining_requests = 6

    def run(task):
        index, ((material, condition), allowed) = task
        intent = allowed[0]
        attempted = set()
        results = []
        seen_sources = set()

        def attempt(provider, purpose, alternative):
            query = search_query(
                provider, material, purpose, pin, alternative, locality
            )
            query_key = provider, query
            if query_key in attempted or research_remaining() <= 0:
                return
            attempted.add(query_key)
            key = ("indexed-query-v2", provider, query)

            def retrieve():
                nonlocal remaining_requests
                with query_guard:
                    if remaining_requests <= 0 or research_remaining() <= 0:
                        return {"status": "budget_exhausted", "rows": [], "services": []}
                    remaining_requests -= 1
                start = time.monotonic()
                try:
                    hits = search_hits(provider, query)
                finally:
                    request_ms.append(round((time.monotonic() - start) * 1000))
                return {"status": "found" if hits else "no_results", "rows": [], "services": [], "hits": hits}

            with query_guard:
                lock = query_locks.setdefault(key, Lock())
            with lock:
                if research_remaining() <= 0:
                    return
                retrieved = research_result(cached, key, retrieve)
            hits = distinct_rows(retrieved.get("hits", []), "url")
            origin = "cached_research" if retrieved["cache_hit"] else "live_research"
            seen_sources.update(hit["url"] for hit in hits)
            rates = indexed_rates(material, condition, pin, purpose, hits)
            rates += published_benchmark_rates(
                material, condition, pin, purpose, hits
            )
            leads = candidate_leads(material, pin, purpose, hits, None)
            results.append({"status": retrieved["status"], "provider": provider[0], "hits": hits,
                            "purpose": purpose, "cached": retrieved["cache_hit"],
                            "rows": [{**row, "provenance": origin} for row in rates],
                            "services": [{**lead, "provenance": origin} for lead in leads]})

        first = providers[index % len(providers)]
        attempt(first, intent, False)
        if not results:
            return material, results, seen_sources
        primary = results[0]
        sufficient = primary["rows"] or any(lead["service_pins"] for lead in primary["services"])
        if not sufficient:
            second = providers[(index + 1) % len(providers)]
            if second != first:
                attempt(second, intent, False)
            elif primary["status"] not in {"unavailable", "budget_exhausted"} and (len(tasks) == 1 or first[0] != "mwmbl"):
                attempt(first, intent, True)
        return material, results, seen_sources

    with ThreadPoolExecutor(max_workers=2) as executor:
        planned = [executor.submit(copy_context().run, run, item) for item in enumerate(tasks)]
        outcomes = [future.result() for future in planned]

    results = [result for _, attempts, _ in outcomes for result in attempts]
    rates = distinct_rows([row for result in results for row in result["rows"]],
                          "material", "condition", "category", "source_url", "observed_on", "unit")
    leads = distinct_rows([lead for result in results for lead in result["services"]],
                          "material", "pathways", "source_url")
    status = "found" if rates or leads else (
        "deadline_reached" if research_remaining() <= 0 else
        "unavailable" if results and all(result["status"] == "unavailable" for result in results) else
        "no_compatible_evidence"
    )
    return {"status": status, "rows": rates, "services": leads, "search_metadata": {
        "provider": providers[0][0],
        "providers": list(dict.fromkeys(result["provider"] for result in results)),
        "indexed_results": len(set().union(*(sources for _, _, sources in outcomes))),
        "attempted_queries": len(results),
        "cached_queries": sum(result["cached"] for result in results),
        "external_requests": len(request_ms), "external_request_ms": sum(request_ms),
    }}



def geographic_evidence(pin, text):
    from core.postal_intelligence import lookup_postal

    if not pin:
        return None

    if re.search(rf"(?<!\d){re.escape(pin)}(?!\d)", text):
        return "published_location"

    postal = lookup_postal(pin)

    if postal.get("status") != "found":
        return None

    states = postal.get("states", [])
    districts = postal.get("districts", [])

    excluded = {
        name.casefold()
        for name in [*states, *districts, "India"]
    }

    localities = [
        part.strip()
        for part in postal.get("locality", "").split(",")
        if part.strip().casefold() not in excluded
    ]

    def mentions(name):
        return len(name) >= 4 and bool(re.search(
            r"\b" + re.escape(name) + r"\b",
            text, re.I
        ))

    if any(mentions(name) for name in localities):
        return "locality_mentioned"

    if any(mentions(name) for name in districts):
        return "district_mentioned"

    return None
