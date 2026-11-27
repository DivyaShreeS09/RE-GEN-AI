"""Import market evidence without automatically trusting external prices."""

import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from core.market_valuation import number


ROOT = Path.home() / "regen-infra"
CATALOGUE = ROOT / "market-evidence.json"
INBOX = ROOT / "market-inbox"


def validate(row):
    if not isinstance(row, dict):
        return False

    required = (
        "material", "condition", "category",
        "unit", "source_url", "observed_on",
    )

    if not all(
        isinstance(row.get(key), str)
        and row[key].strip()
        for key in required
    ):
        return False

    try:
        url = urlparse(row["source_url"])
        observed = date.fromisoformat(
            row["observed_on"]
        )
    except (ValueError, TypeError):
        return False

    if url.scheme != "https" or not url.hostname:
        return False

    if not 0 <= (date.today() - observed).days <= 365:
        return False

    if row["unit"] not in (
        "g", "kg", "tonnes", "pcs", "L"
    ):
        return False

    low = number(row.get("rate_min_inr"))
    high = number(row.get("rate_max_inr"))

    return (
        low is not None
        and high is not None
        and high >= low
    )


def stage_evidence(rows, source_name):
    INBOX.mkdir(parents=True, exist_ok=True)

    accepted = []

    for row in rows:
        if not validate(row):
            continue

        accepted.append({
            **row,
            "reviewed": False,
            "import_source": str(source_name)[:200],
            "imported_on": date.today().isoformat(),
        })

    target = INBOX / "pending-review.json"

    existing = []

    if target.exists():
        existing = json.loads(
            target.read_text(encoding="utf-8-sig")
        )

    combined = existing + accepted

    unique = {}

    for row in combined:
        key = (
            row.get("material"),
            row.get("condition"),
            row.get("category"),
            row.get("unit"),
            row.get("source_url"),
            row.get("observed_on"),
            tuple(row.get("service_pins", [])),
        )
        unique[key] = row

    temporary = target.with_suffix(".tmp")

    temporary.write_text(
        json.dumps(
            list(unique.values()),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    temporary.replace(target)

    return len(accepted)


if __name__ == "__main__":
    ROOT.mkdir(parents=True, exist_ok=True)
    INBOX.mkdir(parents=True, exist_ok=True)

    print("Market evidence inbox ready.")
    print(INBOX)
