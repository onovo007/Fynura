"""Bounded visualization rules using only normalized observations."""

from backend.evidence import fuse_observations
from backend.models.domain import Assessment, VisualizationPoint, VisualizationSpec


def point(o, label=None):
    return VisualizationPoint(
        label=label or o.geography.name,
        value=o.value,
        unit=o.unit,
        evidence_ids=[o.observation_id],
        geography=o.geography.name,
        reporting_cutoff=o.reporting_period_end,
        publication_date=o.publication_date,
        source_id=o.source_id,
        source_url=o.source_url,
    )


def select_visualizations(a: Assessment) -> list[VisualizationSpec]:
    selected = {g.selected_observation_id for g in fuse_observations(a.observations)}
    a = a.model_copy(update={"observations": [o for o in a.observations if o.observation_id in selected]})
    if a.threat_id == "ebola":
        rows = sorted(
            (o for o in a.observations if o.indicator == "confirmed_cases"),
            key=lambda o: o.reporting_period_end,
        )
        if len(rows) < 2:
            return []
        return [
            VisualizationSpec(
                chart_type="trajectory",
                title="Ebola outbreak trajectory",
                subtitle="Confirmed cases across sequential WHO Disease Outbreak News reports",
                threat_id="ebola",
                geography=a.geography.name,
                points=[point(o, o.reporting_period_end.isoformat()) for o in rows],
                supporting_evidence_ids=[o.observation_id for o in rows],
                source_label="World Health Organization, Disease Outbreak News",
                source_url=rows[-1].source_url,
                reporting_cutoff=rows[-1].reporting_period_end,
                retrieved_at=rows[-1].retrieved_at,
                what_this_shows="Cumulative confirmed cases reported in successive compatible WHO updates.",
                what_changed=f"{int(a.delta.get('previous_cases', 0)):,} → {int(a.delta.get('current_cases', 0)):,} reported confirmed cases (+{int(a.delta.get('confirmed_cases', 0)):,}).",
                limitation="Report-to-report changes can include surveillance expansion and retrospective data reconciliation.",
            )
        ]
    if a.threat_id == "measles":
        rows = sorted(
            (o for o in a.observations if o.indicator == "reported_measles_cases"),
            key=lambda o: o.value,
            reverse=True,
        )[:10]
        if len(rows) < 2:
            return []
        return [
            VisualizationSpec(
                chart_type="ranked_bar",
                title="Countries reporting the most measles cases",
                subtitle="Latest sufficiently complete WHO provisional monthly reporting period",
                threat_id="measles",
                geography="Global",
                points=[point(o) for o in rows],
                supporting_evidence_ids=[o.observation_id for o in rows],
                source_label="World Health Organization, Provisional measles and rubella data",
                source_url=rows[0].source_url,
                reporting_cutoff=rows[0].reporting_period_end,
                retrieved_at=rows[0].retrieved_at,
                what_this_shows="Country ranking for the latest month with at least 120 non-null country reports.",
                limitation="WHO states these provisional reports under-represent true occurrence and have an approximately one-to-two-month lag.",
            )
        ]
    global_rows = [o for o in a.observations if o.geography.level == "global"]
    cases = next(
        (o for o in global_rows if o.indicator == "reported_cholera_awd_cases"), None
    )
    if not cases:
        return []
    return [
        VisualizationSpec(
            chart_type="metric_cards",
            title="Global cholera verified metrics",
            subtitle="Cumulative metrics from the latest verified WHO Weekly Epidemiological Record",
            threat_id="cholera",
            geography="Global",
            points=[
                point(o, o.indicator.replace("reported_", "").replace("_", " ").title())
                for o in global_rows
            ],
            supporting_evidence_ids=[o.observation_id for o in global_rows],
            source_label="World Health Organization, Weekly Epidemiological Record",
            source_url=cases.source_url,
            reporting_cutoff=cases.reporting_period_end,
            retrieved_at=cases.retrieved_at,
            what_this_shows="Verified cumulative case, death and reporting-country metrics.",
            limitation="A chart is intentionally not shown because these differently scaled totals do not form a meaningful visual comparison.",
        )
    ]
