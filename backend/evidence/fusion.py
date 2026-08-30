from collections import defaultdict
from urllib.parse import urlparse

from backend.models.domain import EvidenceGroup, Observation

AUTHORITY = {
    "international_health_authority": 1.0,
    "national_health_authority": 1.0,
    "official_surveillance_platform": 0.9,
    "subnational_health_authority": 0.9,
}


def contextual_authority(o: Observation) -> float:
    score = AUTHORITY.get(o.source_type, 0.5)
    if o.geography.level == "country" and o.source_type == "national_health_authority":
        return score + 0.1
    if o.geography.level == "region" and o.source_type == "regional_public_health_authority":
        return score + 0.1
    return score


def fuse_observations(observations: list[Observation]) -> list[EvidenceGroup]:
    buckets = defaultdict(list)
    for o in observations:
        buckets[
            (
                o.threat_id,
                o.indicator,
                o.geography.name.lower(),
                o.case_definition,
                o.unit,
                o.reporting_period_start,
                o.reporting_period_end or o.event_date,
            )
        ].append(o)
    result = []
    for (_, indicator, *_), items in buckets.items():
        values = {o.value for o in items}
        selected = None
        if len(items) == 1:
            selected, status, confidence, reasons, conflicts = (
                items[0],
                "resolved",
                round(
                    0.75 * items[0].extraction_confidence + 0.2 * contextual_authority(items[0]),
                    2,
                ),
                ["single_authoritative_observation"],
                [],
            )
        elif len(values) == 1:
            selected, status, confidence, reasons, conflicts = (
                max(items, key=lambda o: (contextual_authority(o), o.retrieved_at)),
                "resolved",
                0.95,
                ["independent_source_agreement" if len({urlparse(str(o.source_url)).hostname for o in items}) > 1 else "same_authority_agreement", "authority_supported"],
                [],
            )
        else:
            ranked = sorted(
                items,
                key=lambda o: (
                    contextual_authority(o),
                    o.publication_date or o.retrieved_at.date(),
                ),
                reverse=True,
            )
            if (
                contextual_authority(ranked[0]) > contextual_authority(ranked[1])
                and ranked[0].publication_date
                and (
                    not ranked[1].publication_date
                    or ranked[0].publication_date > ranked[1].publication_date
                )
            ):
                selected, status, confidence, reasons, conflicts = (
                    ranked[0],
                    "resolved",
                    0.82,
                    ["newer_higher_authority_update"],
                    [f"Competing reported values: {sorted(values)}"],
                )
            else:
                status, confidence, reasons, conflicts = (
                    "conflicted",
                    0.45,
                    ["unresolved_numeric_disagreement"],
                    [f"Comparable sources report different values: {sorted(values)}"],
                )
        result.append(
            EvidenceGroup(
                indicator=indicator,
                status=status,
                selected_observation_id=selected.observation_id if selected else None,
                confidence=confidence,
                reason_codes=reasons,
                conflicts=conflicts,
                candidate_observation_ids=[o.observation_id for o in items],
                relationship="conflicting" if status == "conflicted" else "same_observation_family",
                source_count=len({o.source_id for o in items}),
                quality_signals={
                    "definition_consistency": len({o.case_definition for o in items}) == 1,
                    "geographic_consistency": len(
                        {(o.geography.level, o.geography.code or o.geography.name) for o in items}
                    )
                    == 1,
                    "source_agreement": len(values) == 1,
                    "reporting_cutoff": str(items[0].reporting_period_end or items[0].event_date),
                },
            )
        )
    return result
