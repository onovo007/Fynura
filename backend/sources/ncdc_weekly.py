"""Allowlisted NCDC weekly-report discovery, retrieval and reviewed extraction."""

from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from io import StringIO
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

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

INDEX_URL = "https://www.ncdc.gov.ng/reports/weekly"
ALLOWED_HOSTS = {"ncdc.gov.ng", "www.ncdc.gov.ng"}
PDF_PATH = re.compile(r"^/themes/common/docs/wers/[A-Za-z0-9_.-]+\.pdf$")
MAX_DOCUMENT_BYTES = 20 * 1024 * 1024


@dataclass(frozen=True)
class NCDCReportCandidate:
    source_url: str
    title: str
    issue: str | None
    reporting_label: str | None
    posted_at: datetime | None


@dataclass(frozen=True)
class RetrievedDocument:
    candidate: NCDCReportCandidate
    content: bytes
    checksum: str
    content_type: str
    retrieved_at: datetime


class NCDCWeeklyReportAdapter:
    source_id = "ncdc_weekly_reports"
    publisher = "Nigeria Centre for Disease Control and Prevention"
    parser_version = "ncdc-weekly-v2"

    @staticmethod
    def _validate_url(url: str, *, pdf: bool = False) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
            raise ValueError("NCDC URL is outside the approved HTTPS host allowlist")
        if pdf and not PDF_PATH.fullmatch(parsed.path):
            raise ValueError("NCDC document path is outside the approved weekly-report route")

    @staticmethod
    def _parse_posted_at(text: str) -> datetime | None:
        value = text.removeprefix("Posted:").strip()
        try:
            return datetime.strptime(value, "%d-%m-%Y %I:%M:%S %p").replace(tzinfo=UTC)
        except ValueError:
            return None

    def parse_index(self, html: str) -> list[NCDCReportCandidate]:
        soup = BeautifulSoup(html, "html.parser")
        candidates: list[NCDCReportCandidate] = []
        seen: set[str] = set()
        for anchor in soup.select('a[href*="/themes/common/docs/wers/"]'):
            url = urljoin(INDEX_URL, anchor.get("href", ""))
            if url in seen:
                continue
            self._validate_url(url, pdf=True)
            container = anchor.find_parent("div", class_="row") or anchor.parent
            title_node = container.find("h3") if container else None
            posted_node = container.find("h5") if container else None
            issue_node = None
            if container:
                issue_node = next(
                    (p for p in container.find_all("p") if p.get_text(" ", strip=True).startswith("Issue:")),
                    None,
                )
            title = title_node.get_text(" ", strip=True) if title_node else "NCDC weekly report"
            issue = issue_node.get_text(" ", strip=True).removeprefix("Issue:").strip() if issue_node else None
            posted = self._parse_posted_at(posted_node.get_text(" ", strip=True)) if posted_node else None
            reporting = title.split(":", 1)[1].strip() if ":" in title else None
            candidates.append(NCDCReportCandidate(url, title, issue, reporting, posted))
            seen.add(url)
        if not candidates:
            raise ValueError("NCDC weekly-report index contained no approved PDF links")
        return candidates

    async def discover(
        self,
        *,
        timeout_seconds: float = 20.0,
        client: httpx.AsyncClient | None = None,
    ) -> list[NCDCReportCandidate]:
        self._validate_url(INDEX_URL)
        headers = {"User-Agent": "Fynura evidence retriever/1.0 (+source provenance)"}
        if client is None:
            async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=False, headers=headers) as owned:
                response = await owned.get(INDEX_URL)
        else:
            response = await client.get(INDEX_URL, headers=headers)
        response.raise_for_status()
        return self.parse_index(response.text)

    async def retrieve(
        self,
        candidate: NCDCReportCandidate,
        *,
        timeout_seconds: float = 30.0,
        max_bytes: int = MAX_DOCUMENT_BYTES,
        client: httpx.AsyncClient | None = None,
    ) -> RetrievedDocument:
        self._validate_url(candidate.source_url, pdf=True)
        headers = {"User-Agent": "Fynura evidence retriever/1.0 (+source provenance)"}
        if client is None:
            async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=False, headers=headers) as owned:
                response = await owned.get(candidate.source_url)
        else:
            response = await client.get(candidate.source_url, headers=headers)
        response.raise_for_status()
        return self.validate_document_response(candidate, response, max_bytes=max_bytes)

    def validate_document_response(
        self,
        candidate: NCDCReportCandidate,
        response: httpx.Response,
        *,
        max_bytes: int = MAX_DOCUMENT_BYTES,
    ) -> RetrievedDocument:
        """Validate a fetched response separately so safety rules are unit-testable."""
        self._validate_url(candidate.source_url, pdf=True)
        response.raise_for_status()
        declared_length = response.headers.get("content-length")
        if declared_length and int(declared_length) > max_bytes:
            raise ValueError("NCDC report exceeds the configured document-size limit")
        content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
        if content_type != "application/pdf" or not response.content.startswith(b"%PDF"):
            raise ValueError("NCDC report response is not a valid PDF")
        if len(response.content) > max_bytes:
            raise ValueError("NCDC report exceeds the configured document-size limit")
        return RetrievedDocument(
            candidate=candidate,
            content=response.content,
            checksum=self.checksum(response.content),
            content_type=content_type,
            retrieved_at=datetime.now(UTC),
        )

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
