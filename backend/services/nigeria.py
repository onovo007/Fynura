import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


@lru_cache
def state_crosswalk() -> dict:
    path = ROOT / "data" / "geography" / "nigeria_states.yaml"
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


@lru_cache
def lga_crosswalk() -> dict:
    path = ROOT / "data" / "geography" / "nigeria_lgas.yaml"
    with path.open(encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    records = data.get("lgas", [])
    if len(records) != 774 or len({item["code"] for item in records}) != 774:
        raise ValueError("Nigeria LGA crosswalk must contain 774 unique codes")
    return data


def _normalise_name(value: str) -> str:
    plain = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", plain.lower()).strip()


def match_lga(name: str, *, state_code: str | None = None) -> dict:
    """Return only deterministic LGA matches; ambiguous names stay unresolved."""
    matches = [
        item for item in lga_crosswalk()["lgas"]
        if _normalise_name(item["name"]) == _normalise_name(name)
        and (state_code is None or item["state_code"] == state_code.zfill(2))
    ]
    if len(matches) == 1:
        return {"status": "matched", "match": matches[0]}
    return {"status": "ambiguous" if matches else "unmatched", "matches": matches}


def availability() -> dict:
    crosswalk = state_crosswalk()
    return {
        "country": "Nigeria",
        "source_id": "ncdc_weekly_reports",
        "status": "validation",
        "operational": False,
        "last_epidemiological_cutoff": None,
        "last_refresh": None,
        "available_levels": ["national"],
        "conditional_levels": ["state", "LGA"],
        "state_crosswalk_records": len(crosswalk["states"]),
        "lga_crosswalk_records": len(lga_crosswalk()["lgas"]),
        "lga_crosswalk_status": "reviewed; report-specific names must still match unambiguously",
        "message": "The official document retriever, report-table fixture and administrative crosswalk are under non-production review. Subnational publication remains disabled until a report-specific match and epidemiological review pass.",
    }
