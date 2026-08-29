from datetime import UTC, date, datetime

from backend.models.domain import Assessment, Geography, Observation
from backend.services.map_data import build_map_data


def observation(threat: str, indicator: str, value: float, geography: Geography) -> Observation:
    return Observation(
        threat_id=threat,
        indicator=indicator,
        value=value,
        unit="persons",
        geography=geography,
        reporting_period_end=date(2026, 6, 28),
        publication_date=date(2026, 8, 7),
        source_id=f"who_{threat}",
        source_url=f"https://www.who.int/{threat}",
        source_type="international_health_authority",
        extraction_method="fixture",
        extraction_confidence=0.99,
        supporting_excerpt="fixture",
        run_id="map-fixture",
    )


def assessment(threat: str, rows: list[Observation]) -> Assessment:
    return Assessment(
        run_id="map-fixture",
        threat_id=threat,
        geography=Geography(name="Global", level="global"),
        evidence_cutoff=datetime(2026, 8, 29, tzinfo=UTC),
        headline="fixture",
        summary="fixture",
        claims=[],
        observations=rows,
        evidence_groups=[],
        evidence_confidence=0.91,
        confidence_details={"level": "HIGH"},
        limitations=["Provisional surveillance data."],
        freshness="fresh",
    )


def test_map_preserves_multiple_threats_in_one_country_and_coverage():
    nigeria = Geography(
        name="Nigeria", level="country", iso2="NG", iso3="NGA", who_region="Africa", latitude=9, longitude=8
    )
    rows = [
        assessment("cholera", [observation("cholera", "reported_cholera_awd_cases", 100, nigeria)]),
        assessment("measles", [observation("measles", "reported_measles_cases", 50, nigeria)]),
    ]
    result = build_map_data(rows)
    assert len(result["countries"]) == 1
    assert {signal["disease"] for signal in result["countries"][0]["signals"]} == {"cholera", "measles"}
    assert result["coverage"]["cholera"]["represented"] == 1
    assert result["coverage"]["measles"]["represented"] == 1


def test_region_and_threat_filters_are_explicit():
    nigeria = Geography(
        name="Nigeria", level="country", iso3="NGA", who_region="Africa", latitude=9, longitude=8
    )
    haiti = Geography(
        name="Haiti", level="country", iso3="HTI", who_region="Americas", latitude=19, longitude=-72
    )
    rows = assessment(
        "cholera",
        [
            observation("cholera", "reported_cholera_awd_cases", 100, nigeria),
            observation("cholera", "reported_cholera_awd_cases", 20, haiti),
        ],
    )
    result = build_map_data([rows], threat="cholera", region="Africa")
    assert [country["iso3"] for country in result["countries"]] == ["NGA"]
    assert result["filters"] == {"threat": "cholera", "region": "Africa", "metric": "signal"}


def test_missing_coordinates_are_disclosed_not_mapped_as_zero():
    unknown = Geography(name="Unresolved country", level="country", iso3="XXX", who_region="Africa")
    result = build_map_data(
        [assessment("cholera", [observation("cholera", "reported_cholera_awd_cases", 7, unknown)])]
    )
    assert result["countries"] == []
    assert len(result["missing_coordinates"]) == 1
    assert result["missing_coordinates"][0]["value"] == 7
