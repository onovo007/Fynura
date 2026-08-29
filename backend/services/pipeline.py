import logging
from uuid import uuid4

from backend.config import get_settings
from backend.epidemiology.metrics import crude_cfr
from backend.evidence import fuse_observations
from backend.models.domain import Assessment, Claim
from backend.sources import WHOCholeraAdapter, WHOEbolaAdapter, WHOMeaslesAdapter

log = logging.getLogger("fynura.pipeline")


class Pipeline:
    def __init__(self, repository):
        self.repository = repository

    async def assess_measles(self) -> Assessment:
        run_id = str(uuid4())
        settings = get_settings()
        adapter = WHOMeaslesAdapter()
        log.info("pipeline_start", extra={"run_id": run_id, "agent": "discovery"})
        candidate, content = await adapter.retrieve(settings.request_timeout_seconds)
        observations = adapter.extract(candidate, content, run_id)
        groups = fuse_observations(observations)
        selected = next(o for o in observations if o.indicator == "reported_measles_cases_global")
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
            headline=f"WHO provisional surveillance reports {int(selected.value):,} measles cases globally",
            summary=f"WHO Member States reported {int(selected.value):,} provisional measles cases for the latest sufficiently complete month. These data under-represent occurrence and have a one-to-two-month reporting lag.",
            claims=[
                Claim(
                    text=f"WHO provisional monthly surveillance reports {int(selected.value):,} measles cases for the period ending {selected.reporting_period_end.isoformat()}.",
                    evidence_ids=[selected.observation_id],
                )
            ],
            observations=observations,
            evidence_groups=groups,
            evidence_confidence=groups[0].confidence,
            limitations=[
                "Authoritative surveillance is provisional and may be revised.",
                "WHO states that reported cases represent only a proportion of true community occurrence.",
                "Recent monthly data are incomplete; Fynura selects the latest month with at least 120 reporting countries.",
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

    async def assess_ebola(self) -> Assessment:
        run_id = str(uuid4())
        adapter = WHOEbolaAdapter()
        documents = await adapter.retrieve(get_settings().request_timeout_seconds)
        observations = adapter.extract(documents, run_id)
        groups = fuse_observations(observations)
        cases = sorted(
            (o for o in observations if o.indicator == "confirmed_cases"),
            key=lambda o: o.reporting_period_end,
        )
        latest, prior = cases[-1], cases[-2]
        latest_at = lambda indicator: next(
            (
                o
                for o in observations
                if o.indicator == indicator
                and o.reporting_period_end == latest.reporting_period_end
            ),
            None,
        )
        deaths, cfr, zones, provinces = map(
            latest_at,
            ("reported_deaths", "crude_cfr", "affected_health_zones", "affected_provinces"),
        )
        delta = {
            "confirmed_cases": latest.value - prior.value,
            "previous_cases": prior.value,
            "current_cases": latest.value,
            "previous_cutoff": prior.reporting_period_end.isoformat(),
            "current_cutoff": latest.reporting_period_end.isoformat(),
        }
        assessment = Assessment(
            run_id=run_id,
            threat_id="ebola",
            geography=latest.geography,
            evidence_cutoff=latest.retrieved_at,
            headline=f"WHO reports {int(latest.value):,} confirmed Ebola cases in the Democratic Republic of the Congo",
            summary=f"The latest WHO Disease Outbreak News reports {int(latest.value):,} confirmed cases and {int(deaths.value):,} deaths through {latest.reporting_period_end:%d %B %Y}. This is an increase of {int(delta['confirmed_cases']):,} reported cases from the preceding compatible WHO report.",
            claims=[
                Claim(
                    text=f"WHO reports {int(latest.value):,} confirmed cases and {int(deaths.value):,} deaths.",
                    evidence_ids=[latest.observation_id, deaths.observation_id],
                )
            ],
            observations=observations,
            evidence_groups=groups,
            evidence_confidence=min(g.confidence for g in groups),
            limitations=[
                "Cumulative observations may include retrospective reconciliation.",
                "Changes between reports do not necessarily represent incident cases during the interval.",
                "This is not medical advice.",
            ],
            freshness="fresh",
            delta=delta,
        )
        assessment.delta.update(
            {
                k: v.value
                for k, v in {"cfr": cfr, "health_zones": zones, "provinces": provinces}.items()
                if v
            }
        )
        self.repository.save_assessment(assessment)
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
