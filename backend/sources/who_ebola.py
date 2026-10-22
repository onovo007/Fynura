import re
from datetime import UTC, datetime

import httpx
from bs4 import BeautifulSoup

from backend.models.domain import Geography, Observation
from backend.services.geography import normalize_country

REPORTS = [
    "2026-DON614",
    "2026-DON616",
    "2026-DON617",
    "2026-DON619",
]
BASE = "https://www.who.int/emergencies/disease-outbreak-news/item/"
ALERT_URL = "https://www.who.int/emergencies/alert-and-response"


class WHOEbolaAdapter:
    source_id = "who_ebola_don"

    async def retrieve(self, timeout: float = 25):
        results = []
        async with httpx.AsyncClient(
            timeout=timeout, follow_redirects=True, headers={"User-Agent": "Fynura/0.3"}
        ) as client:
            for report in REPORTS:
                try:
                    response = await client.get(BASE + report)
                    response.raise_for_status()
                    results.append(
                        (
                            str(response.url),
                            BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True),
                        )
                    )
                except httpx.HTTPError:
                    # One inaccessible historical report must not erase the last
                    # compatible verified sequence. Extraction below still
                    # requires multiple DRC cutoffs.
                    continue
            try:
                response = await client.get(ALERT_URL)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                text = soup.get_text(" ", strip=True)
                cutoff = None
                markers = []
                for row in soup.find_all("tr"):
                    cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["th", "td"])]
                    if not cells:
                        continue
                    if cells[0].startswith("Data as of "):
                        cutoff = cells[0].removeprefix("Data as of ")
                        continue
                    country = cells[0].replace("*", "").replace("#", "").strip()
                    if cutoff and country in {"Democratic Republic of the Congo", "Uganda", "France", "Kenya", "Nigeria"} and len(cells) >= 4:
                        markers.append(
                            "WHO_ALERT_ROW::" + "::".join(
                                [cutoff, country, cells[2].replace(" ", ""), cells[3].replace(" ", "")]
                            )
                        )
                    if country == "Total" and len(cells) >= 4:
                        markers.append(
                            "WHO_ALERT_TOTAL::" + "::".join(
                                [cells[2].replace(" ", ""), cells[3].replace(" ", "")]
                            )
                        )
                results.append((str(response.url), text + " " + " ".join(markers)))
            except httpx.HTTPError:
                # The current table augments, but does not invalidate, the
                # compatible Disease Outbreak News sequence.
                pass
        if len(results) < 2:
            raise ValueError("Too few WHO Ebola reports were retrievable for validation")
        return results

    def extract(self, documents, run_id: str):
        observations = []
        patterns = [
            re.compile(
                r"As of (\d{1,2} \w+ 2026).*?total of\s+([\d ]+) confirmed cases, "
                r"including\s+([\d ]+) deaths.*?CFR\) of\s+([\d.]+)%",
                re.IGNORECASE | re.DOTALL,
            ),
            re.compile(
                r"As of (\d{1,2} \w+ 2026), the country has recorded\s+([\d ]+) "
                r"confirmed cases and\s+([\d ]+) confirmed deaths, corresponding to a "
                r"crude case fatality ratio \(CFR\) of\s+([\d.]+)%",
                re.IGNORECASE | re.DOTALL,
            ),
        ]
        geo = normalize_country(
            "Democratic Republic of the Congo", "COD", "African Region"
        )
        for url, text in documents:
            match = next(
                (candidate for pattern in patterns if (candidate := pattern.search(text[:20000]))),
                None,
            )
            pub = re.search(
                r"(\d{1,2} (?:May|June|July|August|September|October) 2026)", text
            )
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
        observations.extend(self._extract_regional_countries(documents, run_id))
        observations.extend(self._extract_alert_table(documents, run_id))
        if (
            len({
                o.reporting_period_end
                for o in observations
                if o.indicator == "confirmed_cases" and o.geography.iso3 == "COD"
            })
            < 2
        ):
            raise ValueError(
                "Sequential WHO Ebola reports were not extracted; no trajectory was fabricated"
            )
        return observations

    def _extract_alert_table(self, documents, run_id: str) -> list[Observation]:
        """Extract current country totals from WHO's official emergency table."""
        rows: list[Observation] = []
        countries = {
            "Democratic Republic of the Congo": ("COD", "African Region"),
            "Uganda": ("UGA", "African Region"),
            "France": ("FRA", "European Region"),
            "Kenya": ("KEN", "African Region"),
            "Nigeria": ("NGA", "African Region"),
        }
        pattern = re.compile(
            r"WHO_ALERT_ROW::(\d{1,2} \w+ 2026)::([^:]+)::([\d-]+)::([\d-]+)"
        )
        for url, text in documents:
            if "alert-and-response" not in url:
                continue
            for match in pattern.finditer(text):
                cutoff_text, name, cases_text, deaths_text = match.groups()
                if name not in countries or cases_text == "-":
                    continue
                iso3, region = countries[name]
                common = self._country_common(
                    name,
                    iso3,
                    date_text=cutoff_text,
                    publication_date=datetime.now(UTC).date(),
                    url=url,
                    run_id=run_id,
                    who_region=region,
                )
                common.update(
                    source_id="who_ebola_alert",
                    extraction_method="deterministic_who_emergency_table_parser",
                )
                rows.append(
                    Observation(
                        indicator="confirmed_cases",
                        value=float(cases_text),
                        unit="persons",
                        supporting_excerpt=f"WHO emergency table reported {cases_text} confirmed cases in {name}.",
                        **common,
                    )
                )
                if deaths_text != "-":
                    rows.append(
                        Observation(
                            indicator="reported_deaths",
                            value=float(deaths_text),
                            unit="persons",
                            supporting_excerpt=f"WHO emergency table reported {deaths_text} confirmed deaths in {name}.",
                            **common,
                        )
                    )
            total_match = re.search(r"WHO_ALERT_TOTAL::([\d-]+)::([\d-]+)", text)
            if total_match:
                cases_text, deaths_text = total_match.groups()
                cutoffs = [
                    datetime.strptime(match.group(1), "%d %B %Y").date()
                    for match in pattern.finditer(text)
                ]
                common = {
                    "threat_id": "ebola",
                    "geography": Geography(
                        name="WHO affected-country total",
                        level="multi_country",
                        who_region="Global",
                    ),
                    "reporting_period_end": max(cutoffs) if cutoffs else datetime.now(UTC).date(),
                    "publication_date": datetime.now(UTC).date(),
                    "retrieved_at": datetime.now(UTC),
                    "source_id": "who_ebola_alert",
                    "source_url": url,
                    "source_type": "international_health_authority",
                    "case_definition": "laboratory-confirmed Bundibugyo virus disease",
                    "extraction_method": "deterministic_who_emergency_table_total_parser",
                    "extraction_confidence": 0.99,
                    "run_id": run_id,
                    "status": "confirmed",
                    "interval_type": "cumulative",
                }
                rows.append(
                    Observation(
                        indicator="confirmed_cases",
                        value=float(cases_text),
                        unit="persons",
                        supporting_excerpt=f"WHO emergency table reported a total of {cases_text} confirmed cases across affected countries with country-specific reporting cutoffs.",
                        **common,
                    )
                )
                if deaths_text != "-":
                    rows.append(
                        Observation(
                            indicator="reported_deaths",
                            value=float(deaths_text),
                            unit="persons",
                            supporting_excerpt=f"WHO emergency table reported a total of {deaths_text} confirmed deaths across affected countries with country-specific reporting cutoffs.",
                            **common,
                        )
                    )
        return rows

    def _extract_regional_countries(self, documents, run_id: str) -> list[Observation]:
        """Extract explicit country totals that are reported outside the DRC headline."""
        observations: list[Observation] = []
        for url, text in documents:
            publication_match = re.search(
                r"(\d{1,2} (?:September|October) 2026)", text
            )
            publication_date = (
                datetime.strptime(publication_match.group(1), "%d %B %Y").date()
                if publication_match
                else None
            )
            if "2026-DON617" in url:
                cases = re.search(r"20 cases in Uganda", text, re.IGNORECASE)
                deaths = re.search(r"including two in Uganda", text, re.IGNORECASE)
                if cases and deaths:
                    common = self._country_common(
                        "Uganda", "UGA", date_text="7 September 2026",
                        publication_date=publication_date, url=url, run_id=run_id,
                    )
                    observations.extend([
                        Observation(
                            indicator="confirmed_cases", value=20, unit="persons",
                            supporting_excerpt="WHO reported 20 confirmed outbreak-linked cases in Uganda.",
                            **common,
                        ),
                        Observation(
                            indicator="reported_deaths", value=2, unit="persons",
                            supporting_excerpt="WHO reported two deaths among the confirmed cases in Uganda.",
                            **common,
                        ),
                    ])
            if "2026-DON619" in url:
                kenya_case = re.search(
                    r"first laboratory-confirmed imported case of BVD in Kenya",
                    text,
                    re.IGNORECASE,
                )
                kenya_death = re.search(r"subsequently died on 5 October", text, re.IGNORECASE)
                if kenya_case and kenya_death:
                    common = self._country_common(
                        "Kenya", "KEN", date_text="6 October 2026",
                        publication_date=publication_date, url=url, run_id=run_id,
                    )
                    observations.extend([
                        Observation(
                            indicator="confirmed_cases", value=1, unit="persons",
                            supporting_excerpt="WHO reported one laboratory-confirmed imported case in Kenya.",
                            **common,
                        ),
                        Observation(
                            indicator="reported_deaths", value=1, unit="persons",
                            supporting_excerpt="WHO reported that the imported case in Kenya died.",
                            **common,
                        ),
                    ])
        return observations

    def _country_common(
        self,
        name: str,
        iso3: str,
        *,
        date_text: str,
        publication_date,
        url: str,
        run_id: str,
        who_region: str = "African Region",
    ) -> dict:
        return {
            "threat_id": "ebola",
            "geography": normalize_country(name, iso3, who_region),
            "reporting_period_end": datetime.strptime(date_text, "%d %B %Y").date(),
            "publication_date": publication_date,
            "retrieved_at": datetime.now(UTC),
            "source_id": self.source_id,
            "source_url": url,
            "source_type": "international_health_authority",
            "case_definition": "laboratory-confirmed Bundibugyo virus disease",
            "extraction_method": "deterministic_who_don_parser",
            "extraction_confidence": 0.98,
            "run_id": run_id,
            "status": "confirmed",
            "interval_type": "cumulative",
        }
