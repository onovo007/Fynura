"""Parser for explicitly transcribed tables in official NCDC weekly reports.

Live PDF discovery is intentionally outside this adapter. A report must first be
retrieved through an approved route, checksummed, and transcribed with its page
and table identifiers. This makes review possible and prevents a layout change
from silently becoming epidemiological data.
"""

from __future__ import annotations

import csv
import hashlib
from datetime import UTC, date, datetime
from io import StringIO

from backend.models.domain import Geography, Observation

REQUIRED_COLUMNS = {
    "disease",
    "indicator",
    "value",
    "status",
    "interval_type",
    "period_start",
    "period_end",
    "page",
    "table",
}


class NCDCWeeklyReportAdapter:
    source_id = "ncdc_weekly_reports"
    publisher = "Nigeria Centre for Disease Control and Prevention"

    @staticmethod
    def checksum(document_bytes: bytes) -> str:
        return f"sha256:{hashlib.sha256(document_bytes).hexdigest()}"

    def extract_csv(
        self,
        content: str,
        *,
        source_url: str,
        document_checksum: str,
        publication_date: date,
        retrieved_at: datetime,
        run_id: str,
        revision_id: str,
    ) -> list[Observation]:
        reader = csv.DictReader(StringIO(content.strip()))
        if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            missing = sorted(REQUIRED_COLUMNS.difference(reader.fieldnames or []))
            raise ValueError(f"NCDC normalized table is missing columns: {', '.join(missing)}")

        observations: list[Observation] = []
        seen: set[tuple[str, str, str, str]] = set()
        for row_number, row in enumerate(reader, start=2):
            value_text = row["value"].strip()
            if not value_text:
                continue  # missing remains unknown; it is never converted to zero
            key = (row["disease"], row["indicator"], row["period_end"], row["interval_type"])
            if key in seen:
                raise ValueError(f"Duplicate NCDC observation at normalized row {row_number}: {key}")
            seen.add(key)
            observations.append(
                Observation(
                    threat_id=row["disease"].strip().lower(),
                    indicator=row["indicator"].strip(),
                    value=float(value_text),
                    unit=row.get("unit", "persons").strip() or "persons",
                    geography=Geography(
                        name=row.get("geography", "Nigeria").strip() or "Nigeria",
                        level=row.get("admin_level", "country").strip() or "country",
                        code=row.get("geography_code", "NGA").strip() or None,
                        source_name=row.get("geography", "Nigeria").strip() or "Nigeria",
                        iso3="NGA" if (row.get("admin_level", "country") == "country") else None,
                    ),
                    reporting_period_start=date.fromisoformat(row["period_start"]),
                    reporting_period_end=date.fromisoformat(row["period_end"]),
                    publication_date=publication_date,
                    retrieved_at=retrieved_at.astimezone(UTC),
                    source_id=self.source_id,
                    source_url=source_url,
                    source_type="national_health_authority",
                    case_definition=row.get("case_definition", "source-defined").strip(),
                    extraction_method="reviewed_normalized_report_table",
                    extraction_confidence=0.98,
                    supporting_excerpt=row.get("supporting_excerpt", "Official NCDC report table").strip(),
                    run_id=run_id,
                    raw_value=float(value_text),
                    raw_indicator=row["indicator"].strip(),
                    raw_geography=row.get("geography", "Nigeria").strip(),
                    status=row["status"].strip().lower(),
                    interval_type=row["interval_type"].strip().lower(),
                    document_checksum=document_checksum,
                    document_page=int(row["page"]),
                    document_table=row["table"].strip(),
                    revision_id=revision_id,
                    qa_flags=[x for x in row.get("qa_flags", "").split("|") if x],
                    confidence_rationale="Official NCDC aggregate table; normalized values require reviewer approval before operational ingestion.",
                )
            )
        return observations
