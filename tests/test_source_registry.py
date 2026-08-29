from backend.services.source_registry import network_summary, sources


def test_registry_statuses_are_truthful():
    items = {item["source_id"]: item for item in sources()}
    assert items["who_global_surveillance"]["operational"] is True
    assert items["africa_cdc"]["operational"] is False
    assert items["ecdc"]["integration_status"] == "configured"
    assert items["paho"]["integration_status"] == "configured"
    assert network_summary()["operational_feeds"] == 1
