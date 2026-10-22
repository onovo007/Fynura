"""Run a read-only validation of the current official NCDC weekly report."""

from __future__ import annotations

import json

import httpx

from backend.models.source_document import SourceDocument
from backend.repositories.memory import MemoryRepository
from backend.sources.ncdc_weekly import INDEX_URL, NCDCWeeklyReportAdapter


def main() -> None:
    adapter = NCDCWeeklyReportAdapter()
    headers = {"User-Agent": "Fynura evidence retriever/1.0 (+source provenance)"}
    index_response = httpx.get(INDEX_URL, headers=headers, timeout=20, follow_redirects=False)
    index_response.raise_for_status()
    candidate = adapter.parse_index(index_response.text)[0]
    document_response = httpx.get(
        candidate.source_url, headers=headers, timeout=30, follow_redirects=False
    )
    retrieved = adapter.validate_document_response(candidate, document_response)
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
    repository = MemoryRepository()
    duplicate_before = repository.has_source_document(document.checksum)
    repository.save_source_document(document)
    duplicate_after = repository.has_source_document(document.checksum)
    print(json.dumps({
        "document": document.model_dump(mode="json"),
        "duplicate_before": duplicate_before,
        "duplicate_after": duplicate_after,
        "production_write": False,
    }, indent=2))


if __name__ == "__main__":
    main()
