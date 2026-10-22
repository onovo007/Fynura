from backend.services.nigeria import availability, state_crosswalk


def test_nigeria_state_crosswalk_has_36_states_and_fct():
    records = state_crosswalk()["states"]
    assert len(records) == 37
    assert len({item["code"] for item in records}) == 37
    assert next(item for item in records if item["code"] == "37")["name"] == "Federal Capital Territory"


def test_nigeria_availability_does_not_claim_live_operation():
    result = availability()
    assert result["operational"] is False
    assert result["status"] == "validation"
    assert result["last_epidemiological_cutoff"] is None
