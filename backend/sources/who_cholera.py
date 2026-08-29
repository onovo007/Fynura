import re
from datetime import UTC, datetime

import httpx
from bs4 import BeautifulSoup

from backend.models.domain import Geography, Observation, SourceCandidate

URL = "https://www.who.int/publications/journals/weekly-epidemiological-record/wer101-31"


class WHOCholeraAdapter:
    source_id = "who_cholera"

    async def retrieve(self, timeout: float = 20) -> tuple[SourceCandidate, str]:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "Fynura/0.1 public-health intelligence"},
        ) as client:
            response = await client.get(URL)
            response.raise_for_status()
        text = BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True)
        candidate = SourceCandidate(
            source_id=self.source_id,
            url=str(response.url),
            publisher="World Health Organization",
            publication_date=datetime(2026, 8, 7, tzinfo=UTC).date(),
            threat_id="cholera",
            geography=Geography(name="Global", level="global"),
            source_type="international_health_authority",
        )
        return candidate, text

    def extract(self, candidate: SourceCandidate, text: str, run_id: str) -> list[Observation]:
        pattern = r"From 1 January to 28 June 2026, a cumulative total of\s+([\d\s,]+?)\s+cholera and AWD cases and\s+([\d\s,]+?)\s+deaths were reported from\s+(\d+)\s+countries"
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            raise ValueError(
                "WHO report retrieved but its cumulative cholera summary was not recognized; no value was fabricated."
            )
        report_date = datetime(2026, 6, 28, tzinfo=UTC).date()
        common = {
            "threat_id": "cholera",
            "unit": "persons",
            "geography": candidate.geography,
            "reporting_period_start": datetime(2026, 1, 1, tzinfo=UTC).date(),
            "reporting_period_end": report_date,
            "publication_date": candidate.publication_date,
            "retrieved_at": candidate.retrieved_at,
            "source_id": candidate.source_id,
            "source_url": candidate.url,
            "source_type": candidate.source_type,
            "extraction_method": "deterministic_authoritative_page_parser",
            "extraction_confidence": 0.98,
            "supporting_excerpt": match.group(0)[:500],
            "run_id": run_id,
        }
        clean = lambda value: float(re.sub(r"[\s,]", "", value))
        return [
            Observation(
                indicator="reported_cholera_awd_cases",
                value=clean(match.group(1)),
                case_definition="cholera and acute watery diarrhoea as reported to WHO",
                **common,
            ),
            Observation(
                indicator="reported_deaths",
                value=clean(match.group(2)),
                case_definition="cholera-related deaths as reported to WHO",
                **common,
            ),
            Observation(
                indicator="affected_countries",
                value=float(match.group(3)),
                unit="countries",
                case_definition="countries reporting cholera or AWD",
                **{k: v for k, v in common.items() if k != "unit"},
            ),
        ]
