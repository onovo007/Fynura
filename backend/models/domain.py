from datetime import UTC, date, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl


def utcnow() -> datetime:
    return datetime.now(UTC)


class Geography(BaseModel):
    name: str
    level: str
    code: str | None = None


class SourceCandidate(BaseModel):
    source_id: str
    url: HttpUrl
    publisher: str
    publication_date: date | None = None
    retrieved_at: datetime = Field(default_factory=utcnow)
    threat_id: str
    geography: Geography
    source_type: str


class Observation(BaseModel):
    observation_id: str = Field(default_factory=lambda: str(uuid4()))
    threat_id: str
    indicator: str
    value: float
    unit: str
    geography: Geography
    event_date: date | None = None
    reporting_period_start: date | None = None
    reporting_period_end: date | None = None
    publication_date: date | None = None
    retrieved_at: datetime = Field(default_factory=utcnow)
    source_id: str
    source_url: HttpUrl
    source_type: str
    case_definition: str | None = None
    extraction_method: str
    extraction_confidence: float = Field(ge=0, le=1)
    supporting_excerpt: str = Field(max_length=500)
    run_id: str
    raw_value: float | None = None
    raw_indicator: str | None = None
    raw_geography: str | None = None
    raw_case_definition: str | None = None


class DerivedMetric(BaseModel):
    name: str
    value: float | None
    unit: str
    input_observation_ids: list[str]
    explanation: str


class EvidenceGroup(BaseModel):
    evidence_group_id: str = Field(default_factory=lambda: str(uuid4()))
    indicator: str
    status: Literal["resolved", "conflicted", "insufficient"]
    selected_observation_id: str | None = None
    confidence: float = Field(ge=0, le=1)
    reason_codes: list[str]
    conflicts: list[str]
    candidate_observation_ids: list[str]
    relationship: Literal[
        "same_observation_family", "compatible", "complementary", "conflicting", "non_comparable"
    ] = "same_observation_family"
    source_count: int = 1
    quality_signals: dict[str, float | bool | str] = {}


class Claim(BaseModel):
    text: str
    evidence_ids: list[str]


class Assessment(BaseModel):
    assessment_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    threat_id: str
    geography: Geography
    generated_at: datetime = Field(default_factory=utcnow)
    evidence_cutoff: datetime
    headline: str
    summary: str
    claims: list[Claim]
    observations: list[Observation]
    evidence_groups: list[EvidenceGroup]
    derived_metrics: list[DerivedMetric] = []
    evidence_confidence: float
    limitations: list[str]
    freshness: Literal["fresh", "cached"]
    previous_assessment_id: str | None = None
    delta: dict[str, Any] = {}


class Watch(BaseModel):
    watch_id: str = Field(default_factory=lambda: str(uuid4()))
    threat_id: str
    geography: str
    created_at: datetime = Field(default_factory=utcnow)
    active: bool = True
    last_checked: datetime | None = None
    last_assessment_id: str | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    threat_id: str | None = None
    stakeholder_mode: str = "general_public"


class AskResponse(BaseModel):
    answer: str
    evidence_ids: list[str]
    declined: bool = False
    visualization_available: bool = False


class VisualizationPoint(BaseModel):
    label: str
    value: float
    unit: str
    evidence_ids: list[str]
    geography: str
    reporting_cutoff: date | None = None
    publication_date: date | None = None
    source_id: str
    source_url: HttpUrl
    verification_status: str = "verified"


class VisualizationSpec(BaseModel):
    visualization_id: str = Field(default_factory=lambda: str(uuid4()))
    chart_type: Literal["ranked_bar", "trajectory", "metric_cards"]
    title: str
    subtitle: str
    threat_id: str
    geography: str
    points: list[VisualizationPoint]
    supporting_evidence_ids: list[str]
    source_label: str
    source_url: HttpUrl
    reporting_cutoff: date | None = None
    retrieved_at: datetime
    what_this_shows: str
    what_changed: str | None = None
    limitation: str
    downloadable: bool = True
