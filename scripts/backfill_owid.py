"""Download versioned OWID annual surveillance, retaining original WHO attribution."""
import csv
import gzip
import hashlib
import io
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pycountry

DATASETS = {
    "measles_annual": ("measles", "reported-cases-of-measles"),
    "cholera_annual": ("cholera", "number-reported-cases-of-cholera"),
}


def parse_csv(text, digest):
    reader = csv.DictReader(io.StringIO(text))
    fields = [k for k in reader.fieldnames if k not in {"Entity", "Code", "Year"}]
    if len(fields) != 1:
        raise ValueError("Expected exactly one case-count indicator")
    countries = {}
    seen = set()
    for row in reader:
        code = row["Code"]
        if pycountry.countries.get(alpha_3=code) is None:
            continue  # Never mix regional aggregates with countries.
        if not row[fields[0]]:
            continue
        value = float(row[fields[0]])
        if not math.isfinite(value) or value < 0 or not value.is_integer():
            raise ValueError("Invalid reported case count")
        year = str(int(row["Year"]))
        if (code, year) in seen:
            raise ValueError("Duplicate country/year must be resolved before publication")
        seen.add((code, year))
        country = countries.setdefault(code, {"code": code, "name": row["Entity"], "points": []})
        country["points"].append({"period": year, "value": int(value), "status": "reported",
            "evidence_id": f"owid:{digest}:{code}:{year}"})
    for country in countries.values():
        country["points"].sort(key=lambda p: p["period"])
    return sorted(countries.values(), key=lambda c: c["name"])


def main():
    datasets = {}
    archive = Path("tmp/history-source-archive")
    archive.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).isoformat()
    for key, (disease, slug) in DATASETS.items():
        url = f"https://ourworldindata.org/grapher/{slug}"
        payloads = {}
        for suffix in (".csv", ".metadata.json"):
            response = httpx.get(url + suffix + "?csvType=full&useColumnShortNames=false", timeout=90, follow_redirects=True)
            response.raise_for_status()
            digest = hashlib.sha256(response.content).hexdigest()
            (archive / digest).write_bytes(response.content)
            payloads[suffix] = (response, digest)
        response, digest = payloads[".csv"]
        metadata = payloads[".metadata.json"][0].json()
        countries = parse_csv(response.text, digest)
        datasets[key] = {"disease": disease, "title": f"Annual {disease} reported cases (WHO via OWID)",
            "frequency": "annual", "unit": "reported cases", "source": "WHO via Our World in Data",
            "source_url": url, "retrieved_at": now, "publication_date": None,
            "sha256": digest, "metadata_sha256": payloads[".metadata.json"][1],
            "original_metadata": metadata, "countries": countries,
            "limitations": "Annual reported cases, not outbreak-specific totals or current-year surveillance. WHO data processed by Our World in Data; not an independent corroborating authority. Reporting gaps and changes in surveillance remain. Cite WHO and OWID; third-party source terms apply."}
    Path("data/history/owid.json.gz").write_bytes(gzip.compress(json.dumps({"datasets": datasets}).encode(), mtime=0))
    print(json.dumps({k: {"countries": len(v["countries"]), "points": sum(len(c["points"]) for c in v["countries"]),
        "latest": max(p["period"] for c in v["countries"] for p in c["points"])} for k, v in datasets.items()}))


if __name__ == "__main__":
    main()
