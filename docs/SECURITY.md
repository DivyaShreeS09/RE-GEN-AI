# Guardrails & Safety

Security and safety logic is centralized in `core/guardrails.py`. Every API response
includes the prototype disclaimer — this cannot be disabled.

---

## Hazard Suppression

`apply_hazard_guardrail(hazard_level: str)` checks whether the hazard level is
`"critical"` or `"high"`.

**Trigger materials:** e-waste (critical), battery waste (critical), medical waste (critical).

**What happens when triggered:**

1. `estimated_profit_suppressed: true` is returned to the Waste Agent
2. The Waste Agent sets `estimated_recovery: null` — no financial value is calculated
3. A mandatory CPCB warning is injected into the response:

   > *"⚠️ HAZARDOUS WASTE DETECTED: This material requires handling by certified, licensed
   > processors only. Unauthorized disposal may violate CPCB environmental regulations..."*

4. The frontend `WasteAnalyzer` component detects `hazard_warning: true` and replaces
   all pathway value displays with a red compliance notice.

This guardrail **cannot be bypassed** by any user input. The check runs before any financial
calculation.

---

## Quantity Validation

`validate_quantity(quantity_kg: float)` rejects:

| Condition | Error message |
|-----------|--------------|
| `quantity_kg ≤ 0` | "Quantity must be greater than 0 kg." |
| `quantity_kg > 100,000` | "Quantity exceeds 100,000 kg. Break into smaller batches." |

The `POST /analyze/waste` endpoint returns **HTTP 400** with the error message if validation fails.
No agent logic runs on an invalid quantity.

---

## Disclaimer Injection

Every API response includes two mandatory strings from `guardrails.py`:

**`DISCLAIMER` (from `get_disclaimer()`):**
> *"RE:GEN AI is a prototype decision-support system. All values are estimated from simulated
> data for capstone demonstration purposes. This is not professional regulatory, financial, or
> engineering advice. Always consult certified waste management, engineering, and environmental
> professionals before taking action."*

**`SIMULATED_DATA_NOTICE` (from `get_simulated_notice()`):**
> *"Data shown is simulated for demonstration. No real IoT sensors or live systems are connected."*

Both are appended to every endpoint response dict, including `GET /health`.

---

## Forbidden Output Patterns

The following phrases are intentionally avoided in all agent-generated text and UI copy:

| Forbidden | Reason |
|-----------|--------|
| "real-time intelligence" | Misrepresents simulated data as live |
| "revolutionary" | Misleading marketing language |
| "powerful AI" | Vague, hyperbolic |
| "next-generation solution" | Vendor-speak |
| "exact profit" | Financial precision not warranted |

**Required phrases used instead:**
- "simulated smart-campus resource logs"
- "hidden resource loss"
- "agent-prioritized intervention"
- "estimated sustainability impact"
- "decision-support prototype"

---

## Production Security Gaps (Known)

These are known issues in the prototype that must be addressed before any production deployment:

| Gap | Detail |
|-----|--------|
| No authentication | All 7 endpoints are open. Add API keys or OAuth. |
| CORS wildcard | `allow_origins=["*"]` — restrict to frontend domain. |
| No rate limiting | Endpoints are unthrottled. Add middleware (e.g. `slowapi`). |
| No input sanitization | `waste_type` string is used as a dict key after normalization — not a SQL injection risk but validate further for production. |

---

*See also: [API.md](API.md) · [AGENTS.md](AGENTS.md)*
