import re
from datetime import date

import httpx
from bs4 import BeautifulSoup

from backend.models.domain import Geography, Observation, SourceCandidate
from backend.services.geography import normalize_country

URL = "https://www.who.int/publications/journals/weekly-epidemiological-record/wer101-31"
PUBLICATION_DATE = date(2026, 8, 7)
REPORT_START = date(2026, 1, 1)
REPORT_CUTOFF = date(2026, 6, 28)


def _number(value: str) -> float | None:
    cleaned = re.sub(r"[\s,]", "", value)
    if not cleaned or cleaned in {"-", "–", "—"}:
        return None
    return float(cleaned)


def _country(value: str) -> str:
    return re.sub(r"[^A-Za-zÀ-ž .,'()\-]+$", "", value).strip()


class WHOCholeraAdapter:
    source_id = "who_cholera"

    async def retrieve(self, timeout: float = 20) -> tuple[SourceCandidate, str]:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "Fynura/0.4 public-health intelligence"},
        ) as client:
            response = await client.get(URL)
            response.raise_for_status()
        candidate = SourceCandidate(
            source_id=self.source_id,
            url=str(response.url),
            publisher="World Health Organization",
            publication_date=PUBLICATION_DATE,
            threat_id="cholera",
            geography=Geography(name="Global", level="global"),
            source_type="international_health_authority",
        )
        return candidate, response.text

    def extract(self, candidate: SourceCandidate, html: str, run_id: str) -> list[Observation]:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)
        summary = re.search(
            r"From 1 January to 28 June 2026, a cumulative total of\s+([\d\s,]+?)\s+cholera and AWD cases and\s+([\d\s,]+?)\s+deaths were reported from\s+(\d+)\s+countries",
            text,
            re.IGNORECASE,
        )
        table = next(
            (
                table
                for table in soup.find_all("table")
                if "Cases per" in table.get_text(" ", strip=True)
                and "Monthly cases" in table.get_text(" ", strip=True)
            ),
            None,
        )
        if not summary or table is None:
            raise ValueError(
                "WHO report retrieved but its Cholera country table was not recognized; no value was fabricated."
            )
        common = {
            "threat_id": "cholera",
            "reporting_period_start": REPORT_START,
            "reporting_period_end": REPORT_CUTOFF,
            "publication_date": candidate.publication_date,
            "retrieved_at": candidate.retrieved_at,
            "source_id": candidate.source_id,
            "source_url": candidate.url,
            "source_type": candidate.source_type,
            "extraction_method": "deterministic_who_structured_html_table",
            "extraction_confidence": 0.99,
            "run_id": run_id,
        }
        observations: list[Observation] = []
        current_region: str | None = None
        rows = table.find_all("tr")[2:]
        indicators = [
            ("reported_cholera_awd_cases", "cases", "cumulative reported cholera and AWD cases"),
            ("reported_deaths", "deaths", "cumulative reported cholera-related deaths"),
            ("crude_cfr", "percent", "WHO reported crude CFR"),
            ("cases_per_100k", "cases per 100,000", "WHO reported cases per 100,000"),
            ("recent_reported_cases", "cases", "reported cases in the last 28 days"),
            ("recent_reported_deaths", "deaths", "reported deaths in the last 28 days"),
            ("recent_crude_cfr", "percent", "WHO reported crude CFR in the last 28 days"),
            ("monthly_cases_change", "percent change", "monthly change in reported cases"),
            ("monthly_deaths_change", "percent change", "monthly change in reported deaths"),
        ]
        for row in rows:
            cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["th", "td"])]
            if len(cells) == 11:
                current_region, source_country, *values = cells
            elif len(cells) == 10 and current_region:
                source_country, *values = cells
            else:
                continue
            source_country = _country(source_country)
            geography = normalize_country(source_country, who_region=current_region)
            for (indicator, unit, definition), raw in zip(indicators, values, strict=True):
                value = _number(raw)
                if value is None:
                    continue
                observations.append(
                    Observation(
                        indicator=indicator,
                        value=value,
                        unit=unit,
                        geography=geography,
                        case_definition=definition,
                        raw_value=value,
                        raw_indicator=indicator,
                        raw_geography=source_country,
                        supporting_excerpt=f"WHO Table 1: {source_country}; {definition}: {raw}",
                        **common,
                    )
                )
        global_common = {
            **common,
            "geography": candidate.geography,
            "unit": "persons",
            "case_definition": "cholera and acute watery diarrhoea as reported to WHO",
            "supporting_excerpt": summary.group(0)[:500],
        }
        observations.extend(
            [
                Observation(
                    indicator="reported_cholera_awd_cases",
                    value=_number(summary.group(1)) or 0,
                    **global_common,
                ),
                Observation(
                    indicator="reported_deaths",
                    value=_number(summary.group(2)) or 0,
                    **global_common,
                ),
                Observation(
                    indicator="affected_countries",
                    value=float(summary.group(3)),
                    unit="countries",
                    **{k: v for k, v in global_common.items() if k != "unit"},
                ),
            ]
        )
        return observations
