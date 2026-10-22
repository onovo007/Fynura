from datetime import UTC, datetime

from backend.evidence import calculate_confidence, fuse_observations
from backend.models.domain import Assessment, Geography
from backend.services.map_data import build_map_data
from backend.sources.ncdc_ebola import NCDCEbolaAdvisoryAdapter
from backend.sources.who_ebola import WHOEbolaAdapter


def test_who_parser_adds_uganda_and_kenya_country_observations():
    documents = [
        (
            "https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON617",
            (
                "10 September 2026. A cumulative total included 20 cases in Uganda and one "
                "case in France. Overall deaths including two in Uganda."
            ),
        ),
        (
            "https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON619",
            (
                "8 October 2026. The first laboratory-confirmed imported case of BVD in Kenya "
                "was reported and the patient subsequently died on 5 October."
            ),
        ),
    ]
    rows = WHOEbolaAdapter()._extract_regional_countries(documents, "regional-fixture")
    values = {(row.geography.iso3, row.indicator): row.value for row in rows}
    assert values == {
        ("UGA", "confirmed_cases"): 20,
        ("UGA", "reported_deaths"): 2,
        ("KEN", "confirmed_cases"): 1,
        ("KEN", "reported_deaths"): 1,
    }


def test_who_parser_accepts_latest_drc_wording():
    documents = [
        (
            "https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON616",
            (
                "28 August 2026. As of 26 August 2026, a total of 5794 confirmed cases, "
                "including 2786 deaths, corresponding to a crude reported CFR) of 48.1%."
            ),
        ),
        (
            "https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON619",
            (
                "8 October 2026. As of 6 October 2026, the country has recorded 8728 confirmed "
                "cases and 4205 confirmed deaths, corresponding to a crude case fatality ratio "
                "(CFR) of 48.2%."
            ),
        ),
    ]
    rows = WHOEbolaAdapter().extract(documents, "latest-wording")
    latest = max(
        (row for row in rows if row.indicator == "confirmed_cases"),
        key=lambda row: row.reporting_period_end,
    )
    assert latest.value == 8728
    assert latest.reporting_period_end.isoformat() == "2026-10-06"


def test_current_who_emergency_table_supersedes_old_country_totals():
    text = (
        "WHO_ALERT_ROW::18 October 2026::Democratic Republic of the Congo::9552::4602 "
        "WHO_ALERT_ROW::20 October 2026::Kenya::9::1 "
        "WHO_ALERT_ROW::20 October 2026::Nigeria::1::- "
        "WHO_ALERT_ROW::6 July 2026::France::1::- "
        "WHO_ALERT_TOTAL::9583::4605"
    )
    rows = WHOEbolaAdapter()._extract_alert_table(
        [("https://www.who.int/emergencies/alert-and-response", text)],
        "alert-table-fixture",
    )
    values = {(row.geography.iso3, row.indicator): row.value for row in rows}
    assert values[("COD", "confirmed_cases")] == 9552
    assert values[("KEN", "confirmed_cases")] == 9
    assert values[("KEN", "reported_deaths")] == 1
    assert values[("NGA", "confirmed_cases")] == 1
    france = next(row for row in rows if row.geography.iso3 == "FRA")
    assert france.geography.who_region == "Europe"
    assert ("NGA", "reported_deaths") not in values
    assert all(row.source_id == "who_ebola_alert" for row in rows)
    total = [row for row in rows if row.geography.level == "multi_country"]
    assert {(row.indicator, row.value) for row in total} == {
        ("confirmed_cases", 9583),
        ("reported_deaths", 4605),
    }
    assert all(row.reporting_period_end.isoformat() == "2026-10-20" for row in total)


def test_current_who_emergency_table_preserves_all_reported_metrics_and_zeros():
    text = (
        "WHO_ALERT_METRIC_ROW::18 October 2026::Democratic Republic of the Congo::468::9552::4602::-::-::48%::2550 "
        "WHO_ALERT_METRIC_ROW::6 July 2026::France::-::1::0::0::0::-::1 "
        "WHO_ALERT_METRIC_ROW::20 October 2026::Kenya::-::9::1::-::-::11%::- "
        "WHO_ALERT_TOTAL_METRICS::468::9583::4605::1::1::48%::2569"
    )
    rows = WHOEbolaAdapter()._extract_alert_table(
        [("https://www.who.int/emergencies/alert-and-response", text)],
        "complete-alert-table-fixture",
    )
    values = {(row.geography.iso3, row.indicator): row.value for row in rows}
    assert values[("COD", "suspected_cases")] == 468
    assert values[("COD", "recovered_cases")] == 2550
    assert values[("KEN", "crude_cfr")] == 11
    assert values[("FRA", "reported_deaths")] == 0
    assert values[("FRA", "probable_cases")] == 0
    assert ("FRA", "crude_cfr") not in values
    assert values[(None, "probable_deaths")] == 1


def test_drc_trajectory_is_not_replaced_by_same_day_imported_case():
    rows = WHOEbolaAdapter().extract(
        [
            (
                "https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON616",
                (
                    "28 August 2026. As of 26 August 2026, a total of 5794 confirmed cases, "
                    "including 2786 deaths, corresponding to a crude reported CFR) of 48.1%."
                ),
            ),
            (
                "https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON619",
                (
                    "8 October 2026. As of 6 October 2026, the country has recorded 8728 "
                    "confirmed cases and 4205 confirmed deaths, corresponding to a crude case "
                    "fatality ratio (CFR) of 48.2%. The first laboratory-confirmed imported "
                    "case of BVD in Kenya was reported and the patient subsequently died on "
                    "5 October."
                ),
            ),
        ],
        "country-selection",
    )
    drc_cases = sorted(
        (
            row
            for row in rows
            if row.indicator == "confirmed_cases" and row.geography.iso3 == "COD"
        ),
        key=lambda row: row.reporting_period_end,
    )
    assert drc_cases[-1].value == 8728
    assert len([row for row in rows if row.geography.iso3 == "KEN"]) == 2


def test_africa_signal_map_distinguishes_confirmed_activity_and_nigeria_advisory():
    adapter = WHOEbolaAdapter()
    who_rows = adapter._extract_regional_countries(
        [
            (
                "https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON617",
                "10 September 2026. 20 cases in Uganda and including two in Uganda.",
            ),
            (
                "https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON619",
                (
                    "8 October 2026. first laboratory-confirmed imported case of BVD in Kenya; "
                    "the patient subsequently died on 5 October."
                ),
            ),
        ],
        "map-fixture",
    )
    rows = who_rows + NCDCEbolaAdvisoryAdapter().extract_reviewed("map-fixture")
    groups = fuse_observations(rows)
    confidence = calculate_confidence(rows, groups)
    item = Assessment(
        run_id="map-fixture",
        threat_id="ebola",
        geography=Geography(name="Africa", level="region", who_region="Africa"),
        evidence_cutoff=datetime(2026, 10, 22, tzinfo=UTC),
        headline="fixture",
        summary="fixture",
        claims=[],
        observations=rows,
        evidence_groups=groups,
        evidence_confidence=confidence["score"],
        confidence_details=confidence,
        limitations=[],
        freshness="fresh",
    )
    signals = build_map_data([item], threat="ebola", region="Africa", metric="signal")
    countries = {country["iso3"]: country for country in signals["countries"]}
    assert set(countries) == {"KEN", "UGA", "NGA"}
    assert countries["NGA"]["signals"][0]["indicator"] == "preparedness_advisory"
    assert "no confirmed Ebola case" in countries["NGA"]["signals"][0]["interpretation"]
    assert countries["KEN"]["signals"][0]["indicator"] == "confirmed_cases"

    cases = build_map_data([item], threat="ebola", region="Africa", metric="reported_cases")
    assert {country["iso3"] for country in cases["countries"]} == {"KEN", "UGA"}


def test_map_corrects_stale_france_region_before_filtering():
    from tests.test_map_data import assessment, observation

    france = Geography(name="France", level="country", iso3="FRA", who_region="Africa", latitude=46, longitude=2)
    item = assessment("ebola", [observation("ebola", "confirmed_cases", 1, france)])

    assert build_map_data([item], threat="ebola", region="Africa", metric="reported_cases")["countries"] == []
    europe = build_map_data([item], threat="ebola", region="Europe", metric="reported_cases")
    assert europe["countries"][0]["who_region"] == "Europe"
