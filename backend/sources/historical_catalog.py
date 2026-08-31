"""Deterministic historical adapters. Outbreak totals never form an incidence curve."""
import re
from collections import defaultdict

from bs4 import BeautifulSoup

CDC_EBOLA = "https://www.cdc.gov/ebola/outbreaks/index.html"
WHO_CHOLERA = "https://ghoapi.azureedge.net/api/CHOLERA_0000000001"


def ebola_chronology(html, digest):
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main") or soup
    rows, skipped = [], []
    year = None
    for node in main.find_all(["h3", "h4"]):
        title = node.get_text(" ", strip=True)
        if node.name == "h3":
            year = int(title) if re.fullmatch(r"\d{4}", title) else None
            continue
        if year is None or year < 2010:
            continue
        parts = []
        for sibling in node.next_siblings:
            if getattr(sibling, "name", None) in {"h3", "h4"}:
                break
            if hasattr(sibling, "get_text"):
                parts.append(sibling.get_text(" ", strip=True))
        text = " ".join(parts)
        match = re.search(r"Reported number (?:of )?cases:\s*([\d,]+)\*?\s*(?=Reported|$)", text)
        if not match:
            skipped.append({"year": year, "geography": title, "reason": "No unambiguous total in labeled case field"})
            continue
        species = re.search(r"Species:\s*(.*?)\s*Reported number", text)
        rows.append({"period": str(year), "label": f"{year} · {title} · entry {len(rows)+1}",
            "geography": title, "value": int(match.group(1).replace(",", "")),
            "status": "reported", "species": species.group(1) if species else "Not stated",
            "definition": "CDC reported outbreak total; case classifications vary by outbreak",
            "evidence_id": f"{digest}:entry:{len(rows)+1}", "source_url": CDC_EBOLA})
    if not rows:
        raise ValueError("CDC chronology structure changed; no outbreak totals extracted")
    return sorted(rows, key=lambda r: r["period"]), skipped


def cholera_history(rows, digest, names):
    grouped = defaultdict(list)
    for row in rows:
        if row.get("SpatialDimType") != "COUNTRY" or row.get("Dim1") or row.get("Dim2") or row.get("Dim3"):
            continue
        if int(row["TimeDim"]) < 2010:
            continue
        grouped[row["SpatialDim"], str(row["TimeDim"])].append(row)
    countries = defaultdict(list)
    for (code, period), values in sorted(grouped.items()):
        counts = {v.get("NumericValue") for v in values}
        value = next(iter(counts)) if len(counts) == 1 else None
        status = "reported" if isinstance(value, (float, int)) and value >= 0 else "missing or conflicted"
        countries[code].append({"period": period, "value": value if status == "reported" else None,
            "status": status, "evidence_id": f"{digest}:{code}:{period}",
            "source_record_ids": [r["Id"] for r in values]})
    return [{"code": code, "name": names.get(code, code), "points": points}
            for code, points in sorted(countries.items())]
