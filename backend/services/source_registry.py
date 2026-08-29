from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


@lru_cache
def sources() -> list[dict]:
    with (ROOT / "data" / "source_registry" / "sources.yaml").open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)["sources"]


def network_summary() -> dict:
    items = sources()
    return {
        "source_families": len(items),
        "operational_feeds": sum(bool(x["operational"]) for x in items),
        "configured_sources": sum(x["integration_status"] == "configured" for x in items),
    }
