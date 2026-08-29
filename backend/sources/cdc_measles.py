import re
from datetime import UTC, datetime

import httpx
from bs4 import BeautifulSoup

from backend.models.domain import Geography, Observation, SourceCandidate

URL = "https://www.cdc.gov/measles/data-research/index.html"


class CDCMeaslesAdapter:
    source_id = "cdc_measles_cases"

    async def retrieve(self, timeout: float = 20) -> tuple[SourceCandidate, str]:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "Fynura/0.1 public-health research; contact repository maintainers"
            },
        ) as client:
            response = await client.get(URL)
            response.raise_for_status()
        text = BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True)
        candidate = SourceCandidate(
            source_id=self.source_id,
            url=str(response.url),
            publisher="U.S. Centers for Disease Control and Prevention",
            threat_id="measles",
            geography=Geography(name="United States", level="country", code="US"),
            source_type="national_health_authority",
        )
        return candidate, text

    def extract(self, candidate: SourceCandidate, text: str, run_id: str) -> list[Observation]:
        patterns = [
            r"(?:As of|From)\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})[^.]{0,180}?(?:total of\s+)?([\d,]+)\s+(?:confirmed\s+)?measles cases",
            r"([\d,]+)\s+(?:confirmed\s+)?measles cases\s+(?:were|have been)\s+reported[^.]{0,120}?([A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
        ]
        match = re.search(patterns[0], text, re.IGNORECASE)
        reversed_order = False
        if not match:
            match = re.search(patterns[1], text, re.IGNORECASE)
            reversed_order = True
        if not match:
            raise ValueError(
                "CDC page was retrieved but its published measles case wording was not recognized; no value was fabricated."
            )
        raw_value, raw_date = (
            (match.group(1), match.group(2)) if reversed_order else (match.group(2), match.group(1))
        )
        report_date = datetime.strptime(raw_date, "%B %d, %Y").replace(tzinfo=UTC).date()
        excerpt = match.group(0)[:500]
        return [
            Observation(
                threat_id="measles",
                indicator="confirmed_cases",
                value=float(raw_value.replace(",", "")),
                unit="persons",
                geography=candidate.geography,
                event_date=report_date,
                reporting_period_end=report_date,
                publication_date=candidate.publication_date,
                retrieved_at=candidate.retrieved_at,
                source_id=candidate.source_id,
                source_url=candidate.url,
                source_type=candidate.source_type,
                case_definition="CDC reported cases",
                extraction_method="deterministic_authoritative_page_parser",
                extraction_confidence=0.92,
                supporting_excerpt=excerpt,
                run_id=run_id,
            )
        ]
