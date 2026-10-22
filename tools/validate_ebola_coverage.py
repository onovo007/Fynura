"""Read-only validation of WHO Ebola country coverage and NCDC monitoring status."""

import json

import httpx
from bs4 import BeautifulSoup

from backend.sources.ncdc_ebola import NCDCEbolaAdvisoryAdapter
from backend.sources.who_ebola import BASE, REPORTS, WHOEbolaAdapter


def main() -> None:
    headers = {"User-Agent": "Fynura evidence retriever/1.0 (+source provenance)"}
    documents = []
    with httpx.Client(timeout=30, follow_redirects=True, headers=headers) as client:
        for report in REPORTS:
            try:
                response = client.get(BASE + report)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                print(f"Skipped {report}: {type(exc).__name__}")
                continue
            documents.append(
                (
                    str(response.url),
                    BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True),
                )
            )
    rows = WHOEbolaAdapter().extract(documents, "live-validation")
    rows.extend(NCDCEbolaAdvisoryAdapter().extract_reviewed("live-validation"))
    latest = {}
    for row in rows:
        key = (row.geography.iso3, row.indicator)
        prior = latest.get(key)
        if prior is None or row.reporting_period_end > prior.reporting_period_end:
            latest[key] = row
    print(json.dumps([
        {
            "country": row.geography.name,
            "iso3": row.geography.iso3,
            "indicator": row.indicator,
            "value": row.value,
            "unit": row.unit,
            "reporting_cutoff": row.reporting_period_end.isoformat(),
            "source_url": str(row.source_url),
        }
        for row in sorted(latest.values(), key=lambda item: (item.geography.iso3 or "", item.indicator))
    ], indent=2))


if __name__ == "__main__":
    main()
