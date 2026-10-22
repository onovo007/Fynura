"""Contextual population data kept separate from disease observations."""

from datetime import UTC, date, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl, model_validator


class ContextObservation(BaseModel):
    context_observation_id: str = Field(default_factory=lambda: str(uuid4()))
    source_id: str
    context_type: Literal[
        "displacement_stock", "returnee_stock", "migrant_stock", "passenger_flow",
        "aircraft_movement", "aggregated_mobility_change",
    ]
    geography_name: str
    geography_code: str
    geography_level: Literal["country", "admin1", "admin2", "route"]
    origin_code: str | None = None
    destination_code: str | None = None
    reference_start: date | None = None
    reference_end: date
    value: float = Field(ge=0)
    unit: str
    source_url: HttpUrl
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    assessment_round: str | None = None
    method: str
    licence_id: str
    attribution: str
    privacy_classification: Literal["public_aggregate", "restricted_aggregate"]
    validation_status: Literal["quarantined", "fixture_validated", "retrospective_validated", "approved"] = "quarantined"
    limitations: list[str] = []

    @model_validator(mode="after")
    def validate_semantics(self):
        if self.context_type == "migrant_stock" and self.geography_level != "country":
            raise ValueError("UN migrant stock is represented at country level in Phase 1")
        if self.reference_start and self.reference_start > self.reference_end:
            raise ValueError("reference_start must not follow reference_end")
        return self


class ContextSourceLicence(BaseModel):
    licence_id: str
    source_id: str
    status: Literal["public_terms_reviewed", "registration_required", "restricted", "pending_legal_review"]
    permitted_uses: list[str]
    prohibited_uses: list[str]
    attribution_required: bool
    attribution_template: str | None = None
    terms_url: HttpUrl
    reviewed_on: date
    public_display_allowed: bool
    derived_outputs_allowed: bool

