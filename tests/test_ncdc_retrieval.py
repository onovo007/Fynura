from datetime import UTC, datetime

import httpx
import pytest

from backend.models.source_document import SourceDocument
from backend.repositories.memory import MemoryRepository
from backend.sources.ncdc_weekly import NCDCReportCandidate, NCDCWeeklyReportAdapter

PDF_URL = "https://www.ncdc.gov.ng/themes/common/docs/wers/700_1791361960.pdf"

INDEX_HTML = """
<div class="row">
  <a href="/themes/common/docs/wers/700_1791361960.pdf">Download</a>
  <h3>Weekly updates on epidemics in Nigeria: as at 23rd August 2026</h3>
  <h5>Posted: 07-10-2026 09:32:40 AM</h5>
  <p>Issue: Volume 16 No. 34. 14th Sept. 2026</p>
</div>
"""


def test_index_parser_preserves_report_metadata():
    reports = NCDCWeeklyReportAdapter().parse_index(INDEX_HTML)
    assert len(reports) == 1
    assert reports[0].source_url == PDF_URL
    assert reports[0].issue == "Volume 16 No. 34. 14th Sept. 2026"
    assert reports[0].reporting_label == "as at 23rd August 2026"
    assert reports[0].posted_at == datetime(2026, 10, 7, 9, 32, 40, tzinfo=UTC)


def test_document_ledger_deduplicates_by_checksum():
    candidate = NCDCReportCandidate(PDF_URL, "Weekly report", "Issue 34", "23 August", None)
    response = httpx.Response(
        200, content=b"%PDF-1.7\nfixture", headers={"content-type": "application/pdf"},
        request=httpx.Request("GET", PDF_URL),
    )
    repository = MemoryRepository()
    adapter = NCDCWeeklyReportAdapter()
    retrieved = adapter.validate_document_response(candidate, response)
    document = SourceDocument(
        checksum=retrieved.checksum, source_id=adapter.source_id, source_url=PDF_URL,
        title=candidate.title, issue=candidate.issue, reporting_label=candidate.reporting_label,
        retrieved_at=retrieved.retrieved_at, content_type=retrieved.content_type,
        byte_length=len(retrieved.content), parser_version=adapter.parser_version,
    )
    assert repository.has_source_document(document.checksum) is False
    repository.save_source_document(document)
    assert repository.has_source_document(document.checksum) is True
    repository.save_source_document(document)
    assert len(repository.source_documents) == 1


def test_retriever_rejects_non_pdf_response():
    candidate = NCDCReportCandidate(PDF_URL, "Weekly report", None, None, None)
    response = httpx.Response(200, text="not a report", request=httpx.Request("GET", PDF_URL))
    with pytest.raises(ValueError, match="not a valid PDF"):
        NCDCWeeklyReportAdapter().validate_document_response(candidate, response)


def test_retriever_rejects_non_allowlisted_document_url():
    candidate = NCDCReportCandidate("https://example.com/report.pdf", "Report", None, None, None)
    response = httpx.Response(200, content=b"%PDF", request=httpx.Request("GET", PDF_URL))
    with pytest.raises(ValueError, match="allowlist"):
        NCDCWeeklyReportAdapter().validate_document_response(candidate, response)
