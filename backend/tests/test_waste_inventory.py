from datetime import date

import pytest

from fastapi.testclient import TestClient
from main import app


def test_twenty_materials_stream_and_optional_pin(token_for):
    client = TestClient(app, headers={"Authorization": token_for("inventory-fixture"),
                                      "Accept": "application/x-ndjson"})
    items = [{"material": f"Unfamiliar pressed composite {i}", "quantity": 3,
              "unit": "pcs" if i % 2 else "kg", "condition": "used"} for i in range(20)]
    response = client.post("/analyze/waste/inventory", json={"items": items})
    assert response.status_code == 200
    import json
    snapshots = [json.loads(line) for line in response.text.splitlines()]
    assert snapshots[0]["completed_items"] == 0
    assert snapshots[-1]["researched_items"] == 20
    assert all(row["intelligence"]["pathways"] for row in snapshots[-1]["items"])
    assert snapshots[-1]["items"][1]["mass_kg"] is None
    assert snapshots[-1]["items"][0]["mass_kg"] == 3
    assert snapshots[-1]["confirmed_net_inr"] is None
    assert client.post("/analyze/waste/inventory", json={"items": items, "service_pin": "123x"}).status_code == 422
    assert client.post("/analyze/waste/inventory", json={"items": items + items}).status_code == 422


def test_restricted_and_unsuitable_donation(token_for):
    client = TestClient(app, headers={"Authorization": token_for("inventory-safety")})
    base = {"quantity": 1, "unit": "pcs", "research_pathways": ["donate", "sell"]}
    rows = client.post("/analyze/waste/inventory", json={"evidence_only": True, "items": [
        {**base, "material": "Cracked lithium battery", "condition": "good"},
        {**base, "material": "Damaged marquetry stool", "condition": "damaged"},
    ]}).json()["items"]
    assert [p["category"] for p in rows[0]["intelligence"]["pathways"]] == ["professional"]
    assert "donate" not in [p["category"] for p in rows[1]["intelligence"]["pathways"]]


def test_market_evidence_uses_compatible_units_and_keeps_negative_net():
    from core.market_evidence import find_market_evidence
    item = {"material":"sisal press fibre", "condition":"dry", "quantity":700, "unit":"g"}
    evidence = {"material":item["material"], "condition":"dry", "category":"sell", "unit":"kg",
                "source_url":"https://example.org/fixture", "reviewed":True,
                "observed_on":date.today().isoformat(), "scope":"India", "rate_min_inr":20,
                "rate_max_inr":40, "costs_inr":30}
    route = {"category":"sell"}
    estimated = find_market_evidence(item, route, rows=[evidence])
    assert (estimated["minimum_inr"], estimated["maximum_inr"], estimated["net_minimum_inr"]) == (14, 28, -16)
    rate = find_market_evidence({**item, "unit":"pcs"}, route, rows=[evidence])
    assert rate["status"] == "rate_only" and rate["minimum_inr"] is None
    assert find_market_evidence(item, route, rows=[]) is None


def test_reject_new_goods_listings_and_keep_published_purchase_signal():
    from core.recovery_discovery import relevant_listing
    item = {"material":"used rattan ottoman"}
    assert not relevant_listing(item, "sell", {"organization":"Rattan Ottoman Showroom"})
    assert relevant_listing(item, "sell", {"organization":"Second Hand Furniture",
                                            "description":"We buy used rattan furniture."})


def test_provider_failure_retains_conditional_guidance(monkeypatch):
    from core import ai_client, waste_intelligence
    monkeypatch.setattr(ai_client, "inference_enabled", lambda: True)
    monkeypatch.setattr(waste_intelligence, "call_ai", lambda *a, **k: ("", False))
    result = waste_intelligence.investigate_recovery("woven flax filter", 4, "pcs", "used")
    assert result["pathways"] and result["ai_enhanced"] is False

def test_offline_catalogue_adds_evidenced_pathway_for_unfamiliar_material(token_for, monkeypatch, tmp_path):
    import json
    evidence = [{"material":"worn flax loom mat", "condition":"dry", "category":"sell", "unit":"kg",
                 "source_url":"https://example.org/reviewed-fixture", "reviewed":True,
                 "observed_on":date.today().isoformat(), "scope":"India",
                 "rate_min_inr":12, "rate_max_inr":15}]
    catalogue = tmp_path / "market-fixture.json"
    catalogue.write_text(json.dumps(evidence))
    monkeypatch.setenv("REGEN_MARKET_EVIDENCE_FILE", str(catalogue))
    client = TestClient(app, headers={"Authorization": token_for("inventory-catalogue")})
    result = client.post("/analyze/waste/inventory", json={"items":[
        {"material":evidence[0]["material"], "condition":"dry", "quantity":2, "unit":"kg"}]}).json()
    route = result["items"][0]["intelligence"]["pathways"][0]
    assert route["category"] == "sell"
    assert route["valuation"]["minimum_inr"] == 24
    assert route["valuation"]["maximum_inr"] == 30
    assert result["realized_recovery"] is None

def test_approved_feed_fetch_is_cached_and_sends_no_inventory(monkeypatch):
    import json
    import httpx
    from core import market_evidence

    endpoint = "https://example.org/fixture-reviewed-feed"
    monkeypatch.setenv("REGEN_ENV", "development")
    monkeypatch.setenv("REGEN_MARKET_FEED_URL", endpoint)
    requests = []
    row = {"reviewed": True, "material": "fixture press fibre"}

    def serve(request):
        requests.append(request)
        return httpx.Response(200, content=json.dumps([row, {"reviewed":False}]).encode())

    client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kwargs:
                        client(transport=httpx.MockTransport(serve), **kwargs))
    assert market_evidence.configured_market_feed() == [row]
    assert market_evidence.configured_market_feed() == [row]
    assert len(requests) == 1 and str(requests[0].url) == endpoint
    assert requests[0].content == b"" and "authorization" not in requests[0].headers

def test_four_material_acceptance_with_published_references(token_for, monkeypatch):
    from core import market_evidence, market_valuation

    class ReviewDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 11, 27)

    monkeypatch.setattr(market_evidence, "date", ReviewDate)
    monkeypatch.setattr(market_valuation, "date", ReviewDate)
    client = TestClient(app, headers={"Authorization": token_for("acceptance-inventory")})
    rows = [("Old mobiles", 3, "pcs", "damaged"), ("Kids clothes", 6, "pcs", "used"),
            ("Books", 10, "pcs", "used"), ("Paper", 5, "kg", "mixed")]
    response = client.post("/analyze/waste/inventory", json={"service_pin": "600082", "items": [
        {"material": material, "quantity": quantity, "unit": unit, "condition": condition}
        for material, quantity, unit, condition in rows]})
    assert response.status_code == 200
    items = response.json()["items"]
    pathways = [{route["category"]: route for route in item["intelligence"]["pathways"]} for item in items]
    assert set(pathways[0]) == {"professional", "repair", "sell", "recycle"}
    assert all(set(routes) == {"sell", "reuse", "donate", "recycle"} for routes in pathways[1:3])
    assert set(pathways[3]) == {"recycle", "collective"}
    assert pathways[1]["donate"]["valuation"]["maximum_inr"] == 0
    assert pathways[2]["donate"]["valuation"]["minimum_inr"] == 0
    paper = pathways[3]["recycle"]["valuation"]
    assert (paper["minimum_inr"], paper["maximum_inr"], paper["net_minimum_inr"]) == (20, 30, None)
    assert paper["geographic_basis"] == "regional_reference"
    assert items[0]["mass_kg"] is None and not response.json()["verified_option_count"]
    assert pathways[0]["sell"]["public_services"][0]["organization"] == "Cashify Perambur"
    leads = [lead for routes in pathways for route in routes.values() for lead in route["public_services"]]
    assert all(lead["acceptance_confirmed"] is False for lead in leads)

def test_live_source_and_cached_provenance_are_distinct(monkeypatch):
    from types import SimpleNamespace
    from core import market_evidence as market
    from core import public_discovery

    class ReviewDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 11, 27)

    monkeypatch.setattr(market, "date", ReviewDate)
    monkeypatch.setattr(public_discovery, "_CACHE", {})
    monkeypatch.setenv("REGEN_ENV", "development")
    monkeypatch.setenv("REGEN_PUBLIC_MARKET_RESEARCH", "1")
    html = "\n".join(["<!-- product-rate:start --><p>27 Nov 2026 · Kangayam market rate</p>",
                     "<table><th>Coconut shell</th><td>₹20 /kg</td></table>"]).encode()
    monkeypatch.setattr(market, "fetch_public_bytes", lambda url, **kw: html)
    items = [SimpleNamespace(material="Coconut shells")]
    first = market.public_market_research(items, "638701")
    second = market.public_market_research(items, "638701")
    assert first["rows"][0]["provenance"] == "live_research"
    assert second["rows"][0]["provenance"] == "cached_research"
    valuation = market.find_market_evidence({"material":"Coconut shells","quantity":15,"unit":"kg","condition":"used"},
                                           {"category":"sell"}, "638701", rows=first["rows"])
    assert valuation["minimum_inr"] == 300 and valuation["net_minimum_inr"] is None


def test_output_revenue_and_treatment_cost_use_different_bases():
    from core.market_valuation import value_pathway
    item = {"material":"reclaimed timber","condition":"used","quantity":8,"unit":"kg"}
    evidence = {**item, "source_url":"https://example.org/synthetic", "observed_on":date.today().isoformat(),
                "reviewed":True, "rate_min_inr":20, "rate_max_inr":25}
    upcycle = value_pathway(item, {"category":"upcycle"}, {**evidence, "category":"upcycle",
        "value_type":"output_revenue", "output_unit":"pcs", "saleable_output_per_input_unit":0.5,
        "costs_inr":95})
    assert (upcycle["minimum_inr"], upcycle["maximum_inr"], upcycle["net_minimum_inr"]) == (80, 100, -15)
    cost = value_pathway(item, {"category":"professional"}, {**evidence, "category":"professional",
        "value_type":"treatment_cost"})
    assert cost["financial_basis"] == "cost" and cost["net_minimum_inr"] == -200


def test_research_leads_reject_wrong_pin_incompatible_units_and_undersized_lot():
    from core.recovery_discovery import research_service_leads
    item = {"material":"synthetic linen offcuts","condition":"used","quantity":8,"unit":"kg"}
    lead = {"material":item["material"],"pathways":["recycle"],"organization":"Synthetic authorized supplier",
            "source_url":"https://example.org/synthetic","description":"Synthetic acceptance evidence.",
            "unit":"kg","service_pins":["132103"],"minimum_quantity":10,"provenance":"cached_research"}
    assert list(research_service_leads(item, "132103", "recycle", [lead])) == []
    assert list(research_service_leads(item, "638701", "recycle", [{**lead,"minimum_quantity":1}])) == []
    assert list(research_service_leads({**item,"unit":"pcs"}, "132103", "recycle", [{**lead,"minimum_quantity":1}])) == []
    accepted = list(research_service_leads(item, "132103", "recycle", [{**lead,"minimum_quantity":1,"acceptance_confirmed":True}]))
    assert accepted[0]["acceptance_confirmed"] is False and accepted[0]["quantity_documented"]

def test_configured_provider_researches_unfamiliar_material_without_tenant_data(monkeypatch):
    import json
    from types import SimpleNamespace
    from core import market_evidence as market
    from core import public_discovery
    monkeypatch.setenv("REGEN_ENV", "development")
    monkeypatch.setenv("REGEN_MATERIAL_RESEARCH_URL", "https://example.org/synthetic-research")
    monkeypatch.setattr(public_discovery, "_CACHE", {})
    requests = []
    def response(url, *, params):
        requests.append((url, params))
        return json.dumps({"rates":[{"material":"ramie loom ends","reviewed":True}],
                           "services":[{"material":"ramie loom ends"}]}).encode()
    monkeypatch.setattr(market, "fetch_public_bytes", response)
    request = [SimpleNamespace(material="Ramie loom ends"), SimpleNamespace(material="rack@example.org")]
    result = market.public_market_research(request, "132103")
    assert result["rows"][0]["provenance"] == "live_research"
    assert result["services"][0]["provenance"] == "live_research"
    assert requests == [("https://example.org/synthetic-research", {"materials":"ramie loom ends","pin":"132103"})]

def test_inference_budget_fallback_uses_material_capabilities():
    from core.waste_intelligence import investigate_recovery

    def categories(material, condition="used"):
        return {p["category"] for p in investigate_recovery(material, 8, "kg", condition, allow_ai=False)["pathways"]}

    assert categories("Linen weaving trimmings and fabric") == {"reuse","upcycle","recycle","collective"}
    assert categories("Maize stalks") == {"compost","collective"}
    assert categories("Salon sweepings") == {"professional","recycle"}
    assert "reuse" not in categories("Broken wooden stools","damaged")

def test_panipat_reviewed_textile_lead_is_not_verified(token_for):
    client = TestClient(app, headers={"Authorization": token_for("panipat-reference")})
    response = client.post("/analyze/waste/inventory", json={"service_pin":"132103","items":[
        {"material":"Cotton fabric offcuts","quantity":8,"unit":"kg","condition":"used"}]})
    assert response.status_code == 200
    paths = response.json()["items"][0]["intelligence"]["pathways"]
    recycle = next(path for path in paths if path["category"] == "recycle")
    assert recycle["verified_services"] == []
    lead, = recycle["public_services"]
    assert lead["organization"] == "Respun (Kay Gee Enterprises)"
    assert lead["provenance"] == "reviewed_reference"
    assert not lead["acceptance_confirmed"]

def test_kabadify_machine_readable_rates_preserve_grade_and_coverage():
    from core.market_evidence import kabadify_rates, find_market_evidence
    record = {"id":"books","name":"Books","hazardous":False,"category":"paper",
              "pricingMode":"per_kg","unit":"INR/kg","rate":8}
    rows = kabadify_rates({"company":"Kabadify","currency":"INR","source":"ops-published",
        "license":{"url":"https://creativecommons.org/licenses/by/4.0/"},
        "serviceArea":"JP Nagar, Jayanagar, BTM Layout, Bilekahalli",
        "effectiveFrom":date.today().isoformat(),"items":[record,{**record,"hazardous":True}]})
    assert len(rows) == 1
    item = {"material":"Used books","condition":"used","quantity":10,"unit":"kg"}
    route = {"category":"recycle"}
    assert find_market_evidence(item, route, "560078", rows=rows)["minimum_inr"] == 80
    assert find_market_evidence(item, route, "638701", rows=rows) is None
    rate = find_market_evidence({**item,"unit":"pcs"}, route, "560078", rows=rows)
    assert rate["rate_min_inr"] == 8 and rate["minimum_inr"] is None

def test_unified_unknown_identity_preserves_original_and_blocks_unsafe_routes(monkeypatch):
    import json
    from core import material_intelligence as intelligence

    base = {"canonical_material":"invented plastic", "material_family":"plastic", "composition":"pure PET",
            "grade":"premium", "certainty":"unknown", "clarification":"What is the label?",
            "search_material":"pet bottle", "recovery_categories":["donate"], "condition_assessment":"Unknown",
            "hidden_opportunity":"Review first", "pathways":[{"category":"donate","title":"Donate usable stock",
                "recipient_type":"documented recipient","action":"Ask the recipient to review it","limitation":"Check grade"}]}
    result = {"materials":[{"index":0, **base},{"index":1, **base},{"index":19, **base}]}
    monkeypatch.setattr(intelligence, "call_ai", lambda *args, **kwargs: (json.dumps(result), True))
    first, second = intelligence.interpret_inventory([
        {"material":"Assorted violet press liner","quantity":1,"unit":"L","condition":"mixed"},
        {"material":"Cracked battery casing","quantity":2,"unit":"pcs","condition":"used"}])
    assert first["canonical_material"] == "Assorted violet press liner" and first["composition"] == "unknown"
    assert second["recovery_plan"]["pathways"] == []
    assert first["grade"] == "unconfirmed" and first["recovery_plan"]["pathways"] == []

def test_scale_gates_direct_industrial_path_without_documented_acceptance():
    from core.waste_intelligence import investigate_recovery
    small = investigate_recovery("sorghum stems", 2, "kg", "used", allow_ai=False)
    bulk = investigate_recovery("sorghum stems", 2, "tonnes", "used", allow_ai=False)
    assert "industrial_symbiosis" not in {route["category"] for route in small["pathways"]}
    assert "industrial_symbiosis" in {route["category"] for route in bulk["pathways"]}


@pytest.fixture
def regional_postal_dataset(tmp_path, monkeypatch):
    # Synthetic test-only geography; never used as production postal evidence.
    dataset = tmp_path / "postal-fixture.csv"
    dataset.write_text(
        "pincode,officename,district,statename\n"
        "600042,Velachery,Chennai,Tamil Nadu\n"
        "641001,Coimbatore,Coimbatore,Tamil Nadu\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("REGEN_POSTAL_DATASET", str(dataset))


def test_reviewed_regional_coverage_requires_publisher_scope_and_compatible_material(regional_postal_dataset):
    from core.recovery_discovery import published_service_leads

    item = {"material": "cellulose fibre packaging", "original_material": "waste paper cartons"}
    leads = published_service_leads(item, "600042", "recycle")
    assert {row["organization"] for row in leads} == {"Scrap Trove", "Loopy", "Disposcrap"}
    assert all(row["coverage"] == "documented_region" and row["publisher_evidence"]
               and not row["acceptance_confirmed"] for row in leads)
    assert not published_service_leads(item, "641001", "recycle")
    assert not published_service_leads(item, "600042", "repair")
    assert not published_service_leads({**item, "contaminated": True}, "600042", "recycle")
    assert not published_service_leads({"material": "used books"}, "600042", "sell")


def test_reviewed_services_stream_early_and_counts_deduplicate(token_for, regional_postal_dataset):
    import json
    from core.recovery_discovery import maps_search_links

    client = TestClient(app, headers={"Authorization": token_for("regional-catalogue"),
                                      "Accept": "application/x-ndjson"})
    material = {"material": "Waste paper cartons", "quantity": 7, "unit": "kg", "condition": "mixed"}
    response = client.post("/analyze/waste/inventory", json={"service_pin": "600042", "items": [material, material]})
    snapshots = [json.loads(line) for line in response.text.splitlines()]
    initial, final = snapshots[1], snapshots[-1]
    assert initial["items"][0]["intelligence"]["research_status"] == "pending"
    assert initial["public_lead_count"] == final["public_lead_count"] == 3
    assert final["verified_partner_count"] == final["verified_option_count"] == 0
    for row in final["items"]:
        assert row["intelligence"]["research_status"] == "public_leads_found"
        recycle = next(route for route in row["intelligence"]["pathways"] if route["category"] == "recycle")
        assert {lead["organization"] for lead in recycle["public_services"]} == {"Scrap Trove", "Loopy", "Disposcrap"}
        assert recycle["maps_search_links"] == maps_search_links(
            row["material"], "recycle", "600042", row["postal_locality"]["name"])


def test_optional_research_reaches_deadline_while_semantic_batch_is_pending(monkeypatch, token_for):
    import json
    import time
    import main
    from core import material_intelligence, search_research
    from core.public_discovery import research_remaining

    deadline_seen = []
    calls = []
    original = material_intelligence.interpret_inventory

    def semantics(items):
        calls.append(items)
        time.sleep(0.3)
        return original(items)

    def search(*_):
        deadline_seen.append(research_remaining())
        time.sleep(max(0, research_remaining()) + 0.03)
        return {"status": "deadline_reached", "rows": [], "services": []}

    monkeypatch.setattr(main, "INVENTORY_RESEARCH_SECONDS", 0.1)
    monkeypatch.setattr(material_intelligence, "interpret_inventory", semantics)
    monkeypatch.setattr(search_research, "general_research", search)
    client = TestClient(app, headers={"Authorization": token_for("research-deadline"),
                                      "Accept": "application/x-ndjson"})
    response = client.post("/analyze/waste/inventory", json={"service_pin": "641001",
        "items": [{"material": "Banana stems", "quantity": 4, "unit": "kg", "condition": "used"}]})
    snapshots = [json.loads(line) for line in response.text.splitlines()]
    initial_plan = snapshots[1]["items"][0]["intelligence"]
    terminal = next(snapshot for snapshot in snapshots if snapshot.get("researched_items"))
    assert initial_plan["pathways"] and initial_plan["research_status"] == "pending"
    assert 0 < deadline_seen[0] <= 0.1
    assert terminal["items"][0]["intelligence"]["research_status"] == "deadline_reached"
    assert not terminal.get("planned_items")
    assert terminal["research_timings_ms"]["optional_research_ms"] < 220
    assert snapshots[-1]["planned_items"] == 1 and len(calls) == 1
    assert snapshots[-1]["items"][0]["intelligence"]["research_status"] == "deadline_reached"


def test_empty_or_unavailable_provider_produces_terminal_state(monkeypatch, token_for):
    from core import search_research

    client = TestClient(app, headers={"Authorization": token_for("research-provider-status")})
    body = {"service_pin": "641001", "items": [
        {"material": "Banana stems", "quantity": 4, "unit": "kg", "condition": "used"}]}
    for returned, expected in (("unavailable", "provider_unavailable"),
                               ("no_compatible_evidence", "no_compatible_evidence")):
        monkeypatch.setattr(search_research, "general_research", lambda *_: {
            "status": returned, "rows": [], "services": []})
        result = client.post("/analyze/waste/inventory", json=body).json()
        intelligence = result["items"][0]["intelligence"]
        assert intelligence["research_status"] == expected
        assert result["public_lead_count"] == 0
        assert any(route["maps_search_links"] for route in intelligence["pathways"])
