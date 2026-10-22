"""Validated registry for contextual sources and their licence constraints."""

from functools import lru_cache
from pathlib import Path

import yaml

from backend.models.contextual import ContextSourceLicence

ROOT = Path(__file__).resolve().parents[2]


@lru_cache
def contextual_sources() -> list[dict]:
    path = ROOT / "data" / "contextual_sources" / "sources.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["sources"]


@lru_cache
def contextual_licences() -> dict[str, ContextSourceLicence]:
    path = ROOT / "data" / "contextual_sources" / "licences.yaml"
    rows = yaml.safe_load(path.read_text(encoding="utf-8"))["licences"]
    return {row["licence_id"]: ContextSourceLicence.model_validate(row) for row in rows}


def validate_contextual_registry() -> None:
    licences = contextual_licences()
    for source in contextual_sources():
        if source["licence_id"] not in licences:
            raise ValueError(f"Missing licence entry for {source['source_id']}")
        if source["public"] and not licences[source["licence_id"]].public_display_allowed:
            raise ValueError(f"Public source {source['source_id']} lacks public-display permission")
        if source["operational"] and source["validation_status"] != "approved":
            raise ValueError(f"Unapproved contextual source marked operational: {source['source_id']}")

