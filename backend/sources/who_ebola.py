import re
from datetime import UTC, datetime

import httpx
from bs4 import BeautifulSoup

from backend.models.domain import Observation
from backend.services.geography import normalize_country

REPORTS = ["2026-DON608", "2026-DON613", "2026-DON614", "2026-DON615", "2026-DON616"]
BASE = "https://www.who.int/emergencies/disease-outbreak-news/item/"


class WHOEbolaAdapter:
    source_id = "who_ebola_don"

    async def retrieve(self, timeout: float = 25):
        results = []
        async with httpx.AsyncClient(
            timeout=timeout, follow_redirects=True, headers={"User-Agent": "Fynura/0.3"}
        ) as client:
            for report in REPORTS:
                response = await client.get(BASE + report)
                response.raise_for_status()
                results.append(
                    (
                        str(response.url),
                        BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True),
                    )
                )
        return results

    def extract(self, documents, run_id: str):
        observations = []
        pattern = re.compile(
            r"As of (\d{1,2} \w+ 2026).*?total of\s+([\d ]+) confirmed cases, including\s+([\d ]+) deaths.*?CFR\) of\s+([\d.]+)%",
            re.IGNORECASE | re.DOTALL,
        )
        geo = normalize_country(
            "Democratic Republic of the Congo", "COD", "African Region"
        )
        for url, text in documents:
            match = pattern.search(text[:15000])
            pub = re.search(r"(\d{1,2} (?:May|June|July|August) 2026)", text)
            if not match or not pub:
                continue
            cutoff = datetime.strptime(match.group(1), "%d %B %Y").replace(tzinfo=UTC).date()
            published = datetime.strptime(pub.group(1), "%d %B %Y").replace(tzinfo=UTC).date()
            zones = re.search(
                r"(?:expanded to|reported from)\s+(\d+) health zones", text, re.IGNORECASE
            )
            provinces = re.search(
                r"(?:across|stands at)\s+(six|five|\d+)\s+(?:out of \d+ )?provinces",
                text,
                re.IGNORECASE,
            )
            common = {
                "threat_id": "ebola",
                "geography": geo,
                "reporting_period_end": cutoff,
                "publication_date": published,
                "retrieved_at": datetime.now(UTC),
                "source_id": self.source_id,
                "source_url": url,
                "source_type": "international_health_authority",
                "extraction_method": "deterministic_who_don_parser",
                "extraction_confidence": 0.98,
                "run_id": run_id,
                "case_definition": "laboratory-confirmed Bundibugyo virus disease",
            }
            excerpt = match.group(0)[:500]
            observations.extend(
                [
                    Observation(
                        indicator="confirmed_cases",
                        value=float(match.group(2).replace(" ", "")),
                        unit="persons",
                        supporting_excerpt=excerpt,
                        **common,
                    ),
                    Observation(
                        indicator="reported_deaths",
                        value=float(match.group(3).replace(" ", "")),
                        unit="persons",
                        supporting_excerpt=excerpt,
                        **common,
                    ),
                    Observation(
                        indicator="crude_cfr",
                        value=float(match.group(4)),
                        unit="percent",
                        supporting_excerpt=excerpt,
                        **common,
                    ),
                ]
            )
            if zones:
                observations.append(
                    Observation(
                        indicator="affected_health_zones",
                        value=float(zones.group(1)),
                        unit="health zones",
                        supporting_excerpt=zones.group(0),
                        **common,
                    )
                )
            if provinces:
                raw = provinces.group(1).lower()
                value = 6 if raw == "six" else 5 if raw == "five" else float(raw)
                observations.append(
                    Observation(
                        indicator="affected_provinces",
                        value=value,
                        unit="provinces",
                        supporting_excerpt=provinces.group(0),
                        **common,
                    )
                )
        if (
            len({o.reporting_period_end for o in observations if o.indicator == "confirmed_cases"})
            < 2
        ):
            raise ValueError(
                "Sequential WHO Ebola reports were not extracted; no trajectory was fabricated"
            )
        return observations
