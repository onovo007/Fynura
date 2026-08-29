import io
from calendar import monthrange
from datetime import date

import httpx
import openpyxl

from backend.models.domain import Geography, Observation, SourceCandidate
from backend.services.geography import normalize_country

URL = "https://immunizationdata.who.int/docs/librariesprovider21/measles-and-rubella/404-table-web-epi-curve-data.xlsx?sfvrsn=5922ebf7_19"
PORTAL = "https://immunizationdata.who.int/global?topic=Provisional-measles-and-rubella-data"


class WHOMeaslesAdapter:
    source_id = "who_measles_monthly"

    async def retrieve(self, timeout: float = 30):
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(URL, headers={"User-Agent": "Fynura/0.3"})
            response.raise_for_status()
        candidate = SourceCandidate(
            source_id=self.source_id,
            url=PORTAL,
            publisher="World Health Organization",
            threat_id="measles",
            geography=Geography(name="Global", level="global"),
            source_type="international_health_authority",
        )
        return candidate, response.content

    def extract(self, candidate, content: bytes, run_id: str):
        sheet = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)["WEB"]
        rows = [r for r in sheet.iter_rows(min_row=2, values_only=True) if r[3] and r[4]]
        coverage = {}
        for row in rows:
            key = (int(row[3]), int(row[4]))
            coverage[key] = coverage.get(key, 0) + int(row[9] is not None)
        year, month = max(period for period, count in coverage.items() if count >= 120)
        cutoff = date(year, month, monthrange(year, month)[1])
        selected = [r for r in rows if (int(r[3]), int(r[4])) == (year, month) and r[9] is not None]
        common = {
            "threat_id": "measles",
            "unit": "cases",
            "reporting_period_end": cutoff,
            "retrieved_at": candidate.retrieved_at,
            "source_id": self.source_id,
            "source_url": candidate.url,
            "source_type": candidate.source_type,
            "extraction_method": "structured_who_xlsx",
            "extraction_confidence": 0.99,
            "run_id": run_id,
            "case_definition": "WHO provisional measles total by final classification",
        }
        observations = [
            Observation(
                indicator="reported_measles_cases",
                value=float(r[9] or 0),
                geography=normalize_country(str(r[1]), str(r[2]), str(r[0])),
                supporting_excerpt=f"WHO workbook row: {r[1]}, {year}-{month:02d}, measles total {r[9] or 0}",
                **common,
            )
            for r in selected
        ]
        observations.append(
            Observation(
                indicator="reported_measles_cases_global",
                value=sum(o.value for o in observations),
                geography=candidate.geography,
                supporting_excerpt=f"Deterministic sum of {len(observations)} compatible country rows for {year}-{month:02d}",
                **common,
            )
        )
        observations.append(
            Observation(
                indicator="countries_reporting",
                value=float(len(selected)),
                unit="countries",
                geography=candidate.geography,
                supporting_excerpt=f"Countries with a non-null measles total for {year}-{month:02d}",
                **{k: v for k, v in common.items() if k != "unit"},
            )
        )
        return observations
