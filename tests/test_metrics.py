from datetime import date

from backend.epidemiology.metrics import (
    absolute_change,
    affected_geography_change,
    crude_cfr,
    direction_of_change,
    percent_change,
)
from backend.models.domain import Geography, Observation


def obs(value, indicator="confirmed_cases"):
    return Observation(
        threat_id="ebola",
        indicator=indicator,
        value=value,
        unit="persons",
        geography=Geography(name="Example", level="country"),
        event_date=date(2026, 1, 1),
        source_id="who",
        source_url="https://who.int/example",
        source_type="international_health_authority",
        extraction_method="fixture",
        extraction_confidence=1,
        supporting_excerpt="Expert annotated fixture",
        run_id="test",
    )


def test_changes_retain_inputs():
    old, new = obs(100), obs(125)
    assert absolute_change(new, old).value == 25
    assert percent_change(new, old).value == 25
    assert absolute_change(new, old).input_observation_ids == [
        old.observation_id,
        new.observation_id,
    ]


def test_denominator_safeguards():
    assert percent_change(obs(4), obs(0)).value is None
    assert crude_cfr(obs(11, "deaths"), obs(10)).value is None


def test_direction_and_geographies():
    assert direction_of_change(-2) == "decreasing"
    assert affected_geography_change({"A", "B"}, {"A", "C"}) == {"added": ["B"], "removed": ["C"]}
