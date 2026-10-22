"""Metadata for an externally retrieved source document.

The ledger deliberately stores provenance and integrity metadata, not the
publisher's document body. This keeps retrieval auditable without republishing
source files whose reuse terms are not explicit.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SourceDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checksum: str
    source_id: str
    source_url: str
    title: str
    issue: str | None = None
    reporting_label: str | None = None
    posted_at: datetime | None = None
    retrieved_at: datetime
    content_type: str
    byte_length: int = Field(ge=1)
    parser_version: str
    validation_status: str = "retrieved"

