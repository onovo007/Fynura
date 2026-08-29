from collections import defaultdict

from backend.models.domain import EvidenceGroup, Observation

AUTHORITY = {
    "international_health_authority": 1.0,
    "national_health_authority": 1.0,
    "official_surveillance_platform": 0.9,
    "subnational_health_authority": 0.9,
}


def fuse_observations(observations: list[Observation]) -> list[EvidenceGroup]:
    buckets = defaultdict(list)
    for o in observations:
        buckets[
            (
                o.threat_id,
                o.indicator,
                o.geography.name.lower(),
                o.case_definition,
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
                    0.75 * items[0].extraction_confidence
                    + 0.2 * AUTHORITY.get(items[0].source_type, 0.5),
                    2,
                ),
                ["single_authoritative_observation"],
                [],
            )
        elif len(values) == 1:
            selected, status, confidence, reasons, conflicts = (
                max(items, key=lambda o: (AUTHORITY.get(o.source_type, 0.5), o.retrieved_at)),
                "resolved",
                0.95,
                ["independent_source_agreement", "authority_supported"],
                [],
            )
        else:
            ranked = sorted(
                items,
                key=lambda o: (
                    AUTHORITY.get(o.source_type, 0.5),
                    o.publication_date or o.retrieved_at.date(),
                ),
                reverse=True,
            )
            if (
                AUTHORITY.get(ranked[0].source_type, 0.5)
                > AUTHORITY.get(ranked[1].source_type, 0.5)
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
            )
        )
    return result
