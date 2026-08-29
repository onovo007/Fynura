from datetime import date, datetime

from backend.models.domain import DerivedMetric, Observation


def absolute_change(current: Observation, previous: Observation) -> DerivedMetric:
    return DerivedMetric(
        name="absolute_change",
        value=current.value - previous.value,
        unit=current.unit,
        input_observation_ids=[previous.observation_id, current.observation_id],
        explanation="Current reported value minus previous reported value.",
    )


def percent_change(current: Observation, previous: Observation) -> DerivedMetric:
    value = None if previous.value == 0 else (current.value - previous.value) / previous.value * 100
    return DerivedMetric(
        name="percent_change",
        value=value,
        unit="percent",
        input_observation_ids=[previous.observation_id, current.observation_id],
        explanation="Change between reported observations divided by the earlier value; unavailable for a zero denominator.",
    )


def crude_cfr(deaths: Observation, cases: Observation) -> DerivedMetric:
    valid = cases.value > 0 and deaths.value >= 0 and deaths.value <= cases.value
    return DerivedMetric(
        name="crude_case_fatality_ratio",
        value=(deaths.value / cases.value * 100) if valid else None,
        unit="percent",
        input_observation_ids=[deaths.observation_id, cases.observation_id],
        explanation="Reported deaths divided by reported cases; not an adjusted clinical fatality estimate.",
    )


def elapsed_days(later: date | datetime, earlier: date | datetime) -> int:
    if isinstance(later, datetime):
        later = later.date()
    if isinstance(earlier, datetime):
        earlier = earlier.date()
    return (later - earlier).days


def growth_rate(current: Observation, previous: Observation, days: int) -> DerivedMetric:
    value = (
        None
        if previous.value <= 0 or days <= 0
        else ((current.value / previous.value) ** (1 / days) - 1) * 100
    )
    return DerivedMetric(
        name="daily_compound_growth_rate",
        value=value,
        unit="percent_per_day",
        input_observation_ids=[previous.observation_id, current.observation_id],
        explanation=f"Compound change over {days} days between reported observations.",
    )


def direction_of_change(value: float, tolerance: float = 0) -> str:
    return "increasing" if value > tolerance else "decreasing" if value < -tolerance else "stable"


def affected_geography_change(current: set[str], previous: set[str]) -> dict[str, list[str]]:
    return {"added": sorted(current - previous), "removed": sorted(previous - current)}


def recency_days(retrieved: datetime, published: date | None) -> int | None:
    return None if published is None else (retrieved.date() - published).days
