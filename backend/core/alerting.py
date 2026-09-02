"""
Slack webhook alerts for critical/high severity findings (prompt 2.3).

Sends a Slack message when water or energy anomalies are critical/high severity.
Set SLACK_WEBHOOK_URL env var to enable. No-op when not configured.
"""

import os
import json
import urllib.request
import urllib.error


def _get_webhook() -> str | None:
    return os.environ.get("SLACK_WEBHOOK_URL") or None


def send_alert(water_result: dict, energy_result: dict, org_name: str, analysis_id: int | None) -> bool:
    """
    Posts a Slack alert when water or energy severity is critical or high.
    Returns True if an alert was sent, False otherwise.
    """
    webhook = _get_webhook()
    if not webhook:
        return False

    findings = []
    w_sev = water_result.get("severity", "none")
    e_sev = energy_result.get("severity", "none")

    if w_sev in ("critical", "high"):
        findings.append(
            f"*Water:* {w_sev.upper()} — "
            f"{water_result.get('total_wasted_liters', 0):,.0f} L wasted, "
            f"{water_result.get('total_anomaly_readings', 0)} anomalous readings"
        )
    if e_sev in ("critical", "high"):
        findings.append(
            f"*Energy:* {e_sev.upper()} — "
            f"{energy_result.get('total_wasted_kwh', 0):,.1f} kWh wasted, "
            f"Rs. {energy_result.get('estimated_cost_inr', 0):,.0f} cost impact"
        )

    if not findings:
        return False

    id_str = f" (run #{analysis_id})" if analysis_id else ""
    text = (
        f":rotating_light: *RE:GEN AI Alert — {org_name}{id_str}*\n"
        + "\n".join(findings)
    )

    payload = json.dumps({"text": text}).encode()
    req = urllib.request.Request(
        webhook, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False
