import logging
from uuid import uuid4

from backend.config import get_settings
from backend.epidemiology.metrics import crude_cfr
from backend.evidence import fuse_observations
from backend.models.domain import Assessment, Claim
from backend.sources import CDCMeaslesAdapter, WHOCholeraAdapter

log = logging.getLogger("fynura.pipeline")


class Pipeline:
    def __init__(self, repository):
        self.repository = repository

    async def assess_measles(self) -> Assessment:
        run_id = str(uuid4())
        settings = get_settings()
        adapter = CDCMeaslesAdapter()
        log.info("pipeline_start", extra={"run_id": run_id, "agent": "discovery"})
        candidate, content = await adapter.retrieve(settings.request_timeout_seconds)
        observations = adapter.extract(candidate, content, run_id)
        groups = fuse_observations(observations)
        selected = observations[0]
        previous = self.repository.latest_assessment("measles")
        delta = {}
        if previous and previous.observations:
            old = next((o for o in previous.observations if o.indicator == "confirmed_cases"), None)
            if old and old.observation_id != selected.observation_id:
                delta = {
                    "confirmed_cases_reported_change": selected.value - old.value,
                    "from_observation_id": old.observation_id,
                    "to_observation_id": selected.observation_id,
                }
        assessment = Assessment(
            run_id=run_id,
            threat_id="measles",
            geography=selected.geography,
            evidence_cutoff=selected.retrieved_at,
            headline=f"CDC reports {int(selected.value):,} measles cases in the United States",
            summary="This is near-real-time public-health intelligence based on the latest value Fynura could retrieve from the official CDC measles surveillance page. Reporting delays and later revisions are possible.",
            claims=[
                Claim(
                    text=f"CDC reports {int(selected.value):,} measles cases through {selected.reporting_period_end.isoformat()}.",
                    evidence_ids=[selected.observation_id],
                )
            ],
            observations=observations,
            evidence_groups=groups,
            evidence_confidence=groups[0].confidence,
            limitations=[
                "Authoritative surveillance is provisional and may be revised.",
                "A single-source observation is not independent corroboration.",
                "This assessment is not medical advice or an estimate of individual risk.",
            ],
            freshness="fresh",
            previous_assessment_id=previous.assessment_id if previous else None,
            delta=delta,
        )
        self.repository.save_assessment(assessment)
        log.info(
            "pipeline_complete",
            extra={
                "run_id": run_id,
                "assessment_id": assessment.assessment_id,
                "model": settings.fynura_model,
            },
        )
        return assessment

    async def assess_cholera(self) -> Assessment:
        run_id = str(uuid4())
        adapter = WHOCholeraAdapter()
        candidate, content = await adapter.retrieve(get_settings().request_timeout_seconds)
        observations = adapter.extract(candidate, content, run_id)
        groups = fuse_observations(observations)
        cases, deaths, countries = observations
        cfr = crude_cfr(deaths, cases)
        previous = self.repository.latest_assessment("cholera")
        assessment = Assessment(
            run_id=run_id,
            threat_id="cholera",
            geography=cases.geography,
            evidence_cutoff=cases.retrieved_at,
            headline=f"WHO reports {int(cases.value):,} cholera and AWD cases across {int(countries.value)} countries",
            summary=f"WHO's 2026 global update reports {int(cases.value):,} cumulative cholera and acute watery diarrhoea cases and {int(deaths.value):,} deaths through 28 June. These values may be revised and reporting definitions differ across countries.",
            claims=[
                Claim(
                    text=f"WHO reports {int(cases.value):,} cumulative cases and {int(deaths.value):,} deaths through 28 June 2026.",
                    evidence_ids=[cases.observation_id, deaths.observation_id],
                ),
                Claim(
                    text=f"The crude ratio of reported deaths to reported cases is {cfr.value:.2f}%.",
                    evidence_ids=cfr.input_observation_ids,
                ),
            ],
            observations=observations,
            evidence_groups=groups,
            derived_metrics=[cfr],
            evidence_confidence=min(g.confidence for g in groups),
            limitations=[
                "Case definitions and reporting systems differ across countries.",
                "Missing reports do not imply zero cases.",
                "Values may be adjusted retrospectively.",
                "This is not medical advice.",
            ],
            freshness="fresh",
            previous_assessment_id=previous.assessment_id if previous else None,
        )
        self.repository.save_assessment(assessment)
        return assessment
