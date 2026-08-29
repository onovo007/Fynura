from datetime import UTC, date, datetime

from backend.models.domain import Assessment, Claim, EvidenceGroup, Geography, Observation
from backend.services.visualization import select_visualizations


def make(indicator, value):
    return Observation(
        threat_id="cholera",
        indicator=indicator,
        value=value,
        unit="persons",
        geography=Geography(name="Global", level="global"),
        reporting_period_end=date(2026, 6, 28),
        publication_date=date(2026, 8, 7),
        retrieved_at=datetime.now(UTC),
        source_id="who",
        source_url="https://www.who.int/report",
        source_type="international_health_authority",
        extraction_method="fixture",
        extraction_confidence=1,
        supporting_excerpt="fixture",
        run_id="run",
    )


def assessment(observations):
    groups = [
        EvidenceGroup(
            indicator=o.indicator,
            status="resolved",
            selected_observation_id=o.observation_id,
            confidence=0.9,
            reason_codes=["fixture"],
            conflicts=[],
            candidate_observation_ids=[o.observation_id],
        )
        for o in observations
    ]
    return Assessment(
        run_id="run",
        threat_id="cholera",
        geography=Geography(name="Global", level="global"),
        evidence_cutoff=datetime.now(UTC),
        headline="fixture",
        summary="fixture",
        claims=[Claim(text="fixture", evidence_ids=[])],
        observations=observations,
        evidence_groups=groups,
        evidence_confidence=0.9,
        limitations=[],
        freshness="fresh",
    )


def test_selects_supported_comparison_with_lineage():
    cases, deaths = make("reported_cholera_awd_cases", 100), make("reported_deaths", 4)
    result = select_visualizations(assessment([cases, deaths]))
    assert result[0].chart_type == "metric_cards"
    assert result[0].supporting_evidence_ids == [cases.observation_id, deaths.observation_id]


def test_uses_metric_card_for_single_supported_cholera_metric():
    result = select_visualizations(assessment([make("reported_cholera_awd_cases", 100)]))
    assert result[0].chart_type == "metric_cards"
