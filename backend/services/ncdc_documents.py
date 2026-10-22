"""Validation-only NCDC document workflow.

This service discovers and records document metadata. It does not parse a PDF
into epidemiological observations or change the source's operational status.
"""

from backend.models.source_document import SourceDocument
from backend.sources.ncdc_weekly import NCDCReportCandidate, NCDCWeeklyReportAdapter


async def retrieve_and_record(candidate: NCDCReportCandidate, repository, *, client=None) -> tuple[SourceDocument, bool]:
    adapter = NCDCWeeklyReportAdapter()
    retrieved = await adapter.retrieve(candidate, client=client)
    document = SourceDocument(
        checksum=retrieved.checksum,
        source_id=adapter.source_id,
        source_url=candidate.source_url,
        title=candidate.title,
        issue=candidate.issue,
        reporting_label=candidate.reporting_label,
        posted_at=candidate.posted_at,
        retrieved_at=retrieved.retrieved_at,
        content_type=retrieved.content_type,
        byte_length=len(retrieved.content),
        parser_version=adapter.parser_version,
        validation_status="retrieved_not_published",
    )
    duplicate = repository.has_source_document(document.checksum)
    if not duplicate:
        repository.save_source_document(document)
    return document, duplicate
