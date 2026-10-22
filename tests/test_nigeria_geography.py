from backend.services.nigeria import availability, lga_crosswalk, match_lga


def test_lga_crosswalk_has_all_unique_official_codes():
    records = lga_crosswalk()["lgas"]
    assert len(records) == 774
    assert len({item["code"] for item in records}) == 774
    assert all(item["code"][:2] == item["state_code"] for item in records)
    assert {item["state_code"] for item in records} == {f"{number:02d}" for number in range(1, 38)}


def test_lga_match_requires_unique_name_or_state_context():
    assert match_lga("Aba North") == {
        "status": "matched",
        "match": {"code": "0101", "state_code": "01", "name": "Aba North"},
    }
    assert match_lga("Aba North", state_code="02")["status"] == "unmatched"
    assert match_lga("Not A Real LGA")["status"] == "unmatched"


def test_availability_reports_reviewed_crosswalk_without_enabling_publication():
    status = availability()
    assert status["lga_crosswalk_records"] == 774
    assert status["operational"] is False
    assert status["available_levels"] == ["national"]
