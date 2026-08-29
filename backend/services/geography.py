import re
import unicodedata
from functools import lru_cache

from countryinfo import CountryInfo

from backend.models.domain import Geography

WHO_REGIONS = {
    "AFR": "Africa",
    "AMR": "Americas",
    "EUR": "Europe",
    "EMR": "Eastern Mediterranean",
    "SEAR": "South-East Asia",
    "WPR": "Western Pacific",
    "African Region": "Africa",
    "Region of the Americas": "Americas",
    "European Region": "Europe",
    "Eastern Mediterranean Region": "Eastern Mediterranean",
    "South-East Asia Region": "South-East Asia",
    "Western Pacific Region": "Western Pacific",
}

ALIASES = {
    "drc": "Democratic Republic of the Congo",
    "dr congo": "Democratic Republic of the Congo",
    "congo kinshasa": "Democratic Republic of the Congo",
    "democratic republic of congo": "Democratic Republic of the Congo",
    "united republic of tanzania": "Tanzania",
    "ivory coast": "Côte d'Ivoire",
    "cote divoire": "Côte d'Ivoire",
    "cote d ivoire": "Côte d'Ivoire",
    "congo brazzaville": "Republic of the Congo",
    "congo": "Republic of the Congo",
    "bolivia plurinational state of": "Bolivia",
    "iran islamic republic of": "Iran",
    "lao peoples democratic republic": "Laos",
    "syrian arab republic": "Syria",
    "venezuela bolivarian republic of": "Venezuela",
    "viet nam": "Vietnam",
}

OVERRIDES = {
    "cote d ivoire": {
        "name": "Côte d'Ivoire",
        "iso2": "CI",
        "iso3": "CIV",
        "latitude": 8.0,
        "longitude": -5.0,
    },
    "ivory coast": {
        "name": "Côte d'Ivoire",
        "iso2": "CI",
        "iso3": "CIV",
        "latitude": 8.0,
        "longitude": -5.0,
    },
    "myanmar": {
        "name": "Myanmar",
        "iso2": "MM",
        "iso3": "MMR",
        "latitude": 22.0,
        "longitude": 96.0,
    },
    "united kingdom of great britain and northern ireland": {
        "name": "United Kingdom",
        "iso2": "GB",
        "iso3": "GBR",
        "latitude": 54.0,
        "longitude": -2.0,
    },
}

ISO3_OVERRIDES = {"GBR": OVERRIDES["united kingdom of great britain and northern ireland"]}


def _key(value: str) -> str:
    plain = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", plain.lower()).strip()


@lru_cache
def _country_index() -> dict[str, dict]:
    index: dict[str, dict] = {}
    for info in CountryInfo().all().values():
        names = [info.get("name", ""), *(info.get("altSpellings") or [])]
        iso = info.get("ISO") or {}
        names += [iso.get("alpha2", ""), iso.get("alpha3", "")]
        for name in names:
            normalized = _key(str(name)) if name else ""
            if normalized:
                index[normalized] = info
    return index


def normalize_country(source_name: str, iso3: str | None = None, who_region: str | None = None) -> Geography:
    override = ISO3_OVERRIDES.get((iso3 or "").upper()) or OVERRIDES.get(_key(source_name))
    if override:
        return Geography(
            name=override["name"],
            source_name=source_name,
            level="country",
            code=override["iso3"],
            iso2=override["iso2"],
            iso3=override["iso3"],
            who_region=WHO_REGIONS.get(who_region or "", who_region),
            latitude=override["latitude"],
            longitude=override["longitude"],
        )
    lookup = _key(iso3 or "")
    info = _country_index().get(lookup) if lookup else None
    if not info:
        alias = ALIASES.get(_key(source_name), source_name)
        info = _country_index().get(_key(alias))
    if not info:
        return Geography(
            name=source_name,
            source_name=source_name,
            level="country",
            code=iso3,
            iso3=iso3,
            who_region=WHO_REGIONS.get(who_region or "", who_region),
        )
    iso = info.get("ISO") or {}
    latlng = info.get("latlng") or []
    canonical = info.get("name") or source_name
    return Geography(
        name=canonical,
        source_name=source_name,
        level="country",
        code=iso.get("alpha3") or iso3,
        iso2=iso.get("alpha2"),
        iso3=iso.get("alpha3") or iso3,
        who_region=WHO_REGIONS.get(who_region or "", who_region),
        latitude=float(latlng[0]) if len(latlng) == 2 else None,
        longitude=float(latlng[1]) if len(latlng) == 2 else None,
    )
