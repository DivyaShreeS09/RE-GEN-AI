from datetime import date
from types import SimpleNamespace

from core import public_discovery, search_research as search


def test_research_follows_validated_material_scope_and_reports_cache(monkeypatch):
    monkeypatch.setenv("REGEN_ENV", "development")
    monkeypatch.setenv("REGEN_SEARCH_PROVIDER", "mwmbl")
    monkeypatch.setattr(public_discovery, "_CACHE", {})
    queries = []
    def hits(provider, query):
        queries.append((provider[0], query))
        return [{"url":"https://example.org/recovery", "title":"Synthetic Fibre Cooperative",
                 "excerpt":"Our facility buys reclaimed jute webbing in postal area 641001."}]
    monkeypatch.setattr(search, "search_hits", hits)
    item = SimpleNamespace(material="Reclaimed jute webbing", condition="used")
    row = {"intelligence":{"pathways":[{"category":"sell"}]}}
    first = search.general_research([item], "641001", [row])
    second = search.general_research([item], "641001", [row])
    assert first["services"][0]["provenance"] == "live_research"
    assert second["services"][0]["provenance"] == "cached_research"
    assert first["services"][0]["coverage_basis"] == "published_location"
    assert len(queries) == 1 and first["rows"] == []


def test_extraction_cannot_change_publisher_identity_or_coverage():
    hit = {"url":"https://example.org/recovery", "title":"Synthetic Materials Exchange",
           "excerpt":"Our facility buys reclaimed jute webbing near 641001."}
    proposal = search.CandidateEvidence(leads=[{"source":0, "organization":"Fabricated Organization",
                                                "evidence":hit["excerpt"]}])
    assert search.candidate_leads("reclaimed jute webbing", "641001", "sell", [hit], proposal)[0]["organization"] == hit["title"]
    assert not search.candidate_leads("unrelated textile", "641001", "sell", [hit], None)
    assert not search.candidate_leads("reclaimed jute webbing", "638701", "sell", [hit], None)


def test_indexed_rates_require_approved_publisher_and_matching_grade_and_pin(monkeypatch):
    today = date.today().isoformat()
    hit = {"url":"https://example.org/recovery", "title":"Synthetic pulp rate sheet",
           "excerpt":f"{today} · ramie loom offcuts · dry · buying rate: INR 18/kg · 132103"}
    assert search.indexed_rates("ramie loom offcuts", "dry", "132103", "sell", [hit]) == []
    monkeypatch.setenv("REGEN_SEARCH_RATE_HOSTS", "example.org")
    rate, = search.indexed_rates("ramie loom offcuts", "dry", "132103", "sell", [hit])
    assert rate["rate_min_inr"] == "18"
    assert search.indexed_rates("ramie loom offcuts", "used", "132103", "sell", [hit]) == []
    assert search.indexed_rates("ramie loom offcuts", "dry", "641001", "sell", [hit]) == []


def test_link_policy_and_private_endpoint_boundary():
    for value in ("https://localhost/item", "https://10.0.0.1/site", "http://example.org/"):
        assert search.source_url(value) is None
    assert search.source_url("https://example.org/material?tracking=123#fragment") == "https://example.org/material"
    assert search.searx_url("http://127.0.0.1:18888/search") == "http://127.0.0.1:18888/search"

def test_ewaste_indexed_lead_does_not_claim_pin_coverage():
    hit = {"url":"https://example.in/", "title":"E-waste Recycling | Example",
           "excerpt":"Do you need to recycle your e-waste? Check our recycling service."}
    assert search.candidate_leads("e-waste", "560062", "professional", [hit], None) == []

def test_fallback_uses_only_configured_providers_and_deduplicates_inventory(monkeypatch):
    monkeypatch.setenv("REGEN_ENV", "development")
    monkeypatch.setenv("REGEN_SEARCH_PROVIDERS", "mwmbl,searxng,brave,searxng")
    monkeypatch.setenv("REGEN_SEARXNG_URL", "http://127.0.0.1:18888/search")
    monkeypatch.delenv("REGEN_BRAVE_API_KEY", raising=False)
    monkeypatch.setattr(public_discovery, "_CACHE", {})
    calls = []
    def search_hits(provider, query):
        calls.append((provider[0], query))
        if provider[0] == "mwmbl":
            return []
        return [{"url":"https://example.org/v",
                 "title":"Synthetic supplier", "excerpt":"Our business buys compressed coir pith at PIN 688001."}]
    monkeypatch.setattr(search, "search_hits", search_hits)
    items = [SimpleNamespace(material="Compressed coir pith", condition="used")] * 2
    plans = [{"intelligence":{"pathways":[{"category":"sell"}]}}] * 2
    result = search.general_research(items, "688001", plans)
    assert [name for name, _ in calls] == ["mwmbl", "searxng"]
    assert len(result["services"]) == 1
    assert result["search_metadata"]["attempted_queries"] == 2


def test_single_provider_expands_search_once_and_reuses_cached_queries_across_pins(monkeypatch):
    monkeypatch.setenv("REGEN_ENV", "development")
    monkeypatch.setenv("REGEN_SEARCH_PROVIDERS", "mwmbl")
    monkeypatch.setattr(public_discovery, "_CACHE", {})
    calls = []
    monkeypatch.setattr(search, "search_hits", lambda provider, query: calls.append(query) or [])
    items = [SimpleNamespace(material="Hemp combing waste", condition="used")]
    plans = [{"intelligence":{"pathways":[{"category":"sell"}, {"category":"recycle"}]}}]
    first = search.general_research(items, "638701", plans)
    second = search.general_research(items, "132103", plans)
    assert len(set(calls)) == len(calls) == 3
    assert sum("638701" in query for query in calls) == 1
    assert sum("132103" in query for query in calls) == 1
    assert sum("India" in query for query in calls) == 1

    assert first["search_metadata"]["attempted_queries"] == 2
    assert first["search_metadata"]["cached_queries"] == 0
    assert second["search_metadata"]["attempted_queries"] == 2
    assert second["search_metadata"]["cached_queries"] == 1


def test_public_supplier_without_procurement_is_rejected():
    from core.recovery_discovery import attach_local_discovery

    route = {"category": "sell"}
    item = {"material": "banana stems", "condition": "used", "quantity": 2, "unit": "kg"}
    supplier = {"material": "banana stems", "pathways": ["sell"], "service_pins": ["641001"],
                "organization": "Synthetic Product Supplier", "source_url": "https://example.org/products",
                "description": "Manufacturer offering banana stems for purchase online.", "provenance": "live_research"}
    attach_local_discovery(item, {"pathways": [route]}, "641001",
                           {"status": "no_compatible_evidence", "research_services": [supplier]})
    assert route["public_services"] == []
