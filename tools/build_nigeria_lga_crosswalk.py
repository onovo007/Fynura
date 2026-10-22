"""Build the reviewed Nigeria LGA crosswalk from the official NBS metadata page."""

from __future__ import annotations

import re
from pathlib import Path

import httpx
import yaml
from bs4 import BeautifulSoup

SOURCE_URL = "https://microdata.nigerianstat.gov.ng/index.php/catalog/82/variable/V2899"
OUTPUT = Path(__file__).resolve().parents[1] / "data" / "geography" / "nigeria_lgas.yaml"


def extract(html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    records: list[dict[str, str]] = []
    for row in soup.select(".field-var_catgry table tr"):
        cells = [cell.get_text(" ", strip=True) for cell in row.find_all("td")]
        if len(cells) < 2 or not re.fullmatch(r"\d{3,4}", cells[0]):
            continue
        code = cells[0].zfill(4)
        name = re.sub(r"^\d+\.\s*", "", cells[1]).strip().title()
        records.append({"code": code, "state_code": code[:2], "name": name})
    if len(records) != 774:
        raise RuntimeError(f"Expected 774 LGA records, received {len(records)}")
    if len({item['code'] for item in records}) != 774:
        raise RuntimeError("NBS metadata contains duplicate LGA codes")
    return records


def main() -> None:
    response = httpx.get(SOURCE_URL, timeout=30, follow_redirects=False)
    response.raise_for_status()
    payload = {
        "source": "Nigeria National Bureau of Statistics GHS Panel 2023-2024 metadata",
        "source_url": SOURCE_URL,
        "review_status": "reviewed",
        "expected_records": 774,
        "lgas": extract(response.text),
    }
    OUTPUT.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


if __name__ == "__main__":
    main()
