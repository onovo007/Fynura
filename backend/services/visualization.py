"""Deterministic visualization selection from verified assessment evidence."""

from backend.models.domain import Assessment, VisualizationPoint, VisualizationSpec


def select_visualizations(assessment: Assessment) -> list[VisualizationSpec]:
    selected_ids = {
        g.selected_observation_id for g in assessment.evidence_groups if g.status == "resolved"
    }
    verified = [o for o in assessment.observations if o.observation_id in selected_ids]
    by_indicator = {o.indicator: o for o in verified}
    cases = by_indicator.get("reported_cholera_awd_cases")
    deaths = by_indicator.get("reported_deaths")
    if not cases or not deaths or cases.reporting_period_end != deaths.reporting_period_end:
        return []

    points = [
        VisualizationPoint(
            label="Reported cases",
            value=cases.value,
            unit=cases.unit,
            evidence_ids=[cases.observation_id],
            geography=cases.geography.name,
            reporting_cutoff=cases.reporting_period_end,
            publication_date=cases.publication_date,
            source_id=cases.source_id,
            source_url=cases.source_url,
        ),
        VisualizationPoint(
            label="Reported deaths",
            value=deaths.value,
            unit=deaths.unit,
            evidence_ids=[deaths.observation_id],
            geography=deaths.geography.name,
            reporting_cutoff=deaths.reporting_period_end,
            publication_date=deaths.publication_date,
            source_id=deaths.source_id,
            source_url=deaths.source_url,
        ),
    ]
    return [
        VisualizationSpec(
            chart_type="horizontal_bar",
            title="Global cholera reporting snapshot",
            subtitle="Cumulative cholera and acute watery diarrhoea observations in the latest verified WHO report",
            threat_id=assessment.threat_id,
            geography=assessment.geography.name,
            points=points,
            supporting_evidence_ids=[cases.observation_id, deaths.observation_id],
            source_label="World Health Organization, Weekly Epidemiological Record",
            source_url=cases.source_url,
            reporting_cutoff=cases.reporting_period_end,
            retrieved_at=cases.retrieved_at,
            what_this_shows="Reported cumulative cholera/AWD cases and related deaths from the same WHO reporting window.",
            limitation="The values use different indicator scales and are not a time series. Case definitions and reporting completeness differ across countries.",
        )
    ]
