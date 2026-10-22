from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


@lru_cache
def state_crosswalk() -> dict:
    path = ROOT / "data" / "geography" / "nigeria_states.yaml"
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


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
        "lga_crosswalk_status": "requires report-specific NBS code validation before activation",
        "message": "The official NCDC report parser has passed fixture tests. Live retrieval and subnational publication remain disabled until document-level validation is complete.",
    }
