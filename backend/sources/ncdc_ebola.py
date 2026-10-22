"""Reviewed NCDC Ebola preparedness signal for the regional intelligence map."""

from datetime import UTC, date, datetime

from backend.models.domain import Observation
from backend.services.geography import normalize_country


class NCDCEbolaAdvisoryAdapter:
    source_id = "ncdc_ebola_advisory"
    source_url = "https://ncdc.gov.ng/themes/common/docs/protocols/392_1791359525.pdf"

    def extract_reviewed(self, run_id: str) -> list[Observation]:
        return [
            Observation(
                threat_id="ebola",
                indicator="preparedness_advisory",
                value=1,
                unit="official advisory",
                geography=normalize_country("Nigeria", "NGA", "African Region"),
                reporting_period_end=date(2026, 10, 6),
                publication_date=date(2026, 10, 8),
                retrieved_at=datetime.now(UTC),
                source_id=self.source_id,
                source_url=self.source_url,
                source_type="national_health_authority",
                case_definition="preparedness monitoring; no confirmed Ebola case reported",
                extraction_method="reviewed_official_advisory",
                extraction_confidence=0.99,
                supporting_excerpt=(
                    "NCDC reported no confirmed Ebola case in Nigeria and documented national preparedness."
                ),
                run_id=run_id,
                status="reported",
                interval_type="point",
                confidence_rationale="Official NCDC preparedness statement; not a case observation.",
            )
        ]
