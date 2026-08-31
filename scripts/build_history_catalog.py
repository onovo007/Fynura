"""Create a reproducible, source-backed history snapshot for Cloud Run."""
import gzip
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pycountry

from backend.sources.historical_catalog import (
    CDC_EBOLA,
    WHO_CHOLERA,
    cholera_history,
    ebola_chronology,
)
from backend.sources.measles_history import extract_history
from backend.sources.who_measles import PORTAL, URL


def main():
    now = datetime.now(UTC).isoformat()
    archive = Path("tmp/history-source-archive")
    archive.mkdir(parents=True, exist_ok=True)
    manifest = []
    def retrieve(url):
        response = httpx.get(url, timeout=60, follow_redirects=True)
        response.raise_for_status()
        digest = hashlib.sha256(response.content).hexdigest()
        target = archive / digest
        if not target.exists():
            target.write_bytes(response.content)
        manifest.append({"url": url, "sha256": digest, "retrieved_at": now})
        return response, digest
    response, _ = retrieve(URL)
    measles = extract_history(response.content, now)
    mc = [{"code": code, "name": points[-1]["country"],
           "points": [{k: p[k] for k in ("period", "value", "status", "evidence_id", "source_rows")} for p in points]}
          for code, points in sorted(measles["countries"].items())]
    response, digest = retrieve(CDC_EBOLA)
    outbreaks, skipped = ebola_chronology(response.text, digest)
    response, digest = retrieve(WHO_CHOLERA + "?$filter=TimeDim%20ge%202010")
    payload = response.json()
    if payload.get("@odata.nextLink"):
        raise ValueError("WHO response is paginated; refusing incomplete archive")
    cc = cholera_history(payload["value"], digest, {c.alpha_3: c.name for c in pycountry.countries})
    datasets = {
        "measles": {"title": "Monthly measles history", "frequency": "monthly", "source": "WHO",
            "source_url": PORTAL, "unit": "reported cases", "countries": mc,
            "limitations": "Provisional monthly reports; gaps are not zero. Latest source vintage, not historical as-published data. No global sum or validated forecast."},
        "cholera": {"title": "Annual cholera history", "frequency": "annual", "source": "WHO Global Health Observatory",
            "source_url": WHO_CHOLERA, "unit": "reported cases", "countries": cc,
            "limitations": "Annual reported cholera totals. Not directly comparable to partial-year cholera and acute watery diarrhoea reports. Missing years are not zero. Not a monthly early-warning series."},
        "ebola": {"title": "Ebola historical outbreak comparison", "frequency": "outbreak", "source": "CDC",
            "source_url": CDC_EBOLA, "unit": "reported cases per outbreak", "countries": [{"code": "ALL", "name": "Reported outbreak locations", "points": outbreaks}],
            "skipped_entries": skipped,
            "limitations": "Separate outbreak totals grouped by CDC chronology year, not annual incidence. Some outbreaks span multiple years. Species, geography and case definitions differ; no connecting trend or growth calculation. Entries without an unambiguous case total are omitted."}}
    for data in datasets.values():
        data["retrieved_at"] = now
        data["publication_date"] = None
    target = Path("data/history/catalog.json.gz")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(gzip.compress(json.dumps({"version": "history-1.0", "sources": manifest, "datasets": datasets}).encode(), mtime=0))
    print(json.dumps({key: {"countries": len(d["countries"]), "points": sum(len(c["points"]) for c in d["countries"]), "first": min(p["period"] for c in d["countries"] for p in c["points"]), "last": max(p["period"] for c in d["countries"] for p in c["points"])} for key, d in datasets.items()}, indent=2))


if __name__ == "__main__":
    main()
