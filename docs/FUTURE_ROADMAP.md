# Future Roadmap & Known Limitations

## Roadmap

These are identified directions for extending the prototype. **None are currently implemented.**

### Near-Term (Architecture-Ready)

**Live IoT Integration**
Replace `simulation.py` CSV loaders with real-time sensor streams from smart meters, flow
sensors, and occupancy detectors. The agent pipeline is stream-compatible — only `simulation.py`
needs replacement. All agent logic and scoring remains unchanged.

**Quantity Validation Improvements**
Extend `validate_quantity()` to fuzzy-match `waste_type` strings against the knowledge base and
return the closest match if an unknown material is submitted, rather than returning no result.

**Authentication Layer**
Add API key or OAuth 2.0 middleware to `main.py`. All endpoints are currently open.

### Medium-Term (New Features)

**Predictive Analytics**
Add time-series forecasting (ARIMA or lightweight LSTM) to project anomaly likelihood 48–72 hours
ahead, rather than only reporting on historical data.

**Expanded Waste Knowledge Base**
The current 30-material JSON can scale to hundreds of materials. Replace the exact key-lookup in
`waste_agent.py` with a vector similarity search (e.g. `sentence-transformers`) to handle
free-text material descriptions.

**Real-Time WebSocket Dashboard**
Convert the current scan-on-demand model to a WebSocket-based live dashboard that refreshes as
new sensor readings arrive, without requiring a full page-level scan.

**Multi-Campus Architecture**
Extend the API to accept a `campus_id` parameter. Each campus gets its own data store; the same
7-agent pipeline serves all campuses from a single deployment.

### Long-Term (Strategic)

**Smart City Integration**
Export agent outputs in FIWARE NGSI-LD format, compatible with municipal smart city platforms.
Campus sustainability data could feed city-level carbon dashboards.

**Mobile Application**
A React Native or PWA wrapper around the existing API. Priority notifications for critical
anomalies would be pushed to campus sustainability officers via FCM.

---

## Known Limitations

| Limitation | Detail |
|------------|--------|
| Simulated data only | All sensor data is from a static CSV (Jan 15–21, 2024). No live IoT. |
| Rule-based reasoning | No ML. All agent decisions are deterministic threshold rules. |
| Fixed knowledge base | 30 hardcoded materials. Unknown inputs return close-match suggestions, not analysis. |
| No authentication | All endpoints are unauthenticated. Do not deploy publicly without auth. |
| Waste type validation | `/analyze/waste` validates quantity bounds but relies on string normalization for type matching. |
| Estimates only | All INR values are computed from fixed market-rate constants. No live pricing API. |
| Water cost constant | ₹0.05/L is a representative campus rate. Actual rates vary by institution and region. |
| Energy cost constant | ₹8.00/kWh is a standard Indian grid tariff. Commercial rates may differ. |
| CO₂ constants | India grid factor 0.82 kg/kWh (2024 average). Water CO₂ 0.001 kg/L is a simplified estimate. |
| Feasibility scores fixed | Water=9, Energy=8, Waste=7 are hardcoded in the Decision Engine. Real feasibility depends on campus conditions. |
| Waste recovery potential fixed | Set to 60 (simulated baseline) in the Score Agent regardless of actual waste type submitted. |

---

## Contributing

1. Fork the repository and create a branch: `git checkout -b feature/your-feature`
2. Keep backend changes in `backend/` and frontend changes in `frontend/`
3. New agents: create a file in `backend/agents/` and wire it into `main.py`
4. Do not weaken or remove guardrail logic in `core/guardrails.py`
5. All API responses must continue to include `disclaimer` and `data_notice` fields
6. Run `cd frontend && npm run build` and confirm a clean build before opening a PR

---

*See also: [ARCHITECTURE.md](ARCHITECTURE.md) · [SECURITY.md](SECURITY.md)*
