from backend.services.geography import normalize_country


def test_country_aliases_resolve_to_stable_codes_and_coordinates():
    cases = [
        ("DRC", "COD"),
        ("United Republic of Tanzania", "TZA"),
        ("Ivory Coast", "CIV"),
        ("Myanmar", "MMR"),
        ("United Kingdom of Great Britain and Northern Ireland", "GBR"),
    ]
    for source_name, iso3 in cases:
        geography = normalize_country(source_name)
        assert geography.iso3 == iso3
        assert geography.latitude is not None
        assert geography.longitude is not None


def test_source_country_name_is_preserved():
    geography = normalize_country("United Republic of Tanzania", who_region="African Region")
    assert geography.source_name == "United Republic of Tanzania"
    assert geography.name == "Tanzania"
    assert geography.who_region == "Africa"
