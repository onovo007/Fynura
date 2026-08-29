from backend.evidence.fusion import contextual_authority
from backend.models.domain import EvidenceGroup, Observation

MODEL = "fynura-evidence-confidence-v1"
WEIGHTS = {
    "source_authority": 0.20,
    "source_independence": 0.10,
    "source_agreement": 0.15,
    "recency": 0.15,
    "reporting_completeness": 0.12,
    "definition_consistency": 0.08,
    "temporal_consistency": 0.07,
    "geographic_consistency": 0.05,
    "provenance_completeness": 0.08,
}


def _recency(observations: list[Observation]) -> float:
    ages = []
    for item in observations:
        cutoff = item.reporting_period_end or item.event_date or item.publication_date
        if cutoff:
            ages.append(max(0, (item.retrieved_at.date() - cutoff).days))
    if not ages:
        return 0.35
    age = min(ages)
    if age <= 14:
        return 1.0
    if age <= 45:
        return 0.85
    if age <= 90:
        return 0.7
    if age <= 180:
        return 0.5
    return 0.25


def calculate_confidence(observations: list[Observation], groups: list[EvidenceGroup]) -> dict:
    if not observations:
        return {"score": 0.0, "level": "INSUFFICIENT", "components": {}, "model": MODEL}
    source_ids = {item.source_id for item in observations}
    resolved = [group for group in groups if group.status == "resolved"]
    conflicted = [group for group in groups if group.status == "conflicted"]
    complete = [
        item
        for item in observations
        if item.source_url and item.source_id and item.supporting_excerpt and item.extraction_method
    ]
    components = {
        "source_authority": min(
            1.0, sum(contextual_authority(x) for x in observations) / len(observations)
        ),
        "source_independence": min(1.0, 0.55 + 0.2 * (len(source_ids) - 1)),
        "source_agreement": max(0.0, (len(resolved) - 1.5 * len(conflicted)) / max(1, len(groups))),
        "recency": _recency(observations),
        "reporting_completeness": sum(
            bool(x.reporting_period_end or x.event_date) for x in observations
        )
        / len(observations),
        "definition_consistency": sum(
            bool(g.quality_signals.get("definition_consistency", False)) for g in groups
        )
        / max(1, len(groups)),
        "temporal_consistency": sum(bool(g.quality_signals.get("reporting_cutoff")) for g in groups)
        / max(1, len(groups)),
        "geographic_consistency": sum(
            bool(g.quality_signals.get("geographic_consistency", False)) for g in groups
        )
        / max(1, len(groups)),
        "provenance_completeness": len(complete) / len(observations),
    }
    score = round(sum(components[name] * weight for name, weight in WEIGHTS.items()), 3)
    level = "HIGH" if score >= 0.85 else "MODERATE" if score >= 0.65 else "LIMITED"
    limitations = []
    if len(source_ids) == 1:
        limitations.append("Only one independent source authority supports this evidence package.")
    if conflicted:
        limitations.append("At least one comparable evidence group has unresolved conflict.")
    if components["recency"] < 0.7:
        limitations.append("The reporting cutoff is stale relative to retrieval.")
    return {
        "score": score,
        "level": level,
        "components": {key: round(value, 3) for key, value in components.items()},
        "model": MODEL,
        "source_count": len(source_ids),
        "evidence_group_count": len(groups),
        "limitations": limitations,
    }
