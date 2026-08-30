"""One canonical, non-additive evidence contract for all analytical components."""
from urllib.parse import urlparse

from backend.evidence import fuse_observations


def workspace(assessments, threat="all", region="Global", country="", period=""):
    pool = [o for a in assessments if threat == "all" or a.threat_id == threat for o in a.observations]
    country_options = {o.geography.iso3: {"code": o.geography.iso3, "name": o.geography.name}
                       for o in pool if o.geography.iso3 and o.geography.level == "country"
                       and (region == "Global" or o.geography.who_region == region)}
    schema = {"countries": sorted(country_options.values(), key=lambda c: c["name"]),
              "regions": sorted({o.geography.who_region for o in pool if o.geography.who_region}),
              "periods": sorted({str(o.reporting_period_end) for o in pool if o.reporting_period_end}, reverse=True),
              "available_dimensions": [d for d, exists in (
                  ("country", bool(country_options)), ("who_region", any(o.geography.who_region for o in pool)),
                  ("reporting_period", any(o.reporting_period_end for o in pool))) if exists]}
    output, history = [], []
    for a in assessments:
        if threat != "all" and a.threat_id != threat:
            continue
        rows = [o for o in a.observations
                if (not country or o.geography.iso3 == country)
                and (region == "Global" or o.geography.who_region == region)
                and (not period or str(o.reporting_period_end) == period)]
        groups = fuse_observations(rows)
        by_id = {o.observation_id: o for o in rows}
        history.extend(by_id[g.selected_observation_id].model_dump(mode="json") for g in groups
                       if g.selected_observation_id and (country or region != "Global" or
                       by_id[g.selected_observation_id].geography.name == a.geography.name))
        candidates = []
        for g in groups:
            sample = by_id[g.candidate_observation_ids[0]]
            selected = by_id.get(g.selected_observation_id)
            candidates.append((sample, selected, g))
        latest = {}
        for sample, selected, group in candidates:
            key = (sample.geography.name, sample.indicator, sample.unit, sample.case_definition)
            if key not in latest or str(sample.reporting_period_end) > str(latest[key][0].reporting_period_end):
                latest[key] = (sample, selected, group)
        for sample, selected, g in latest.values():
            # Global view prefers source-provided global totals, never sums country reports.
            if not country and region == "Global" and sample.geography.name != a.geography.name:
                continue
            primary = selected or sample
            all_candidates = [by_id[i] for i in g.candidate_observation_ids]
            sources = sorted({urlparse(str(o.source_url)).hostname for o in all_candidates})
            output.append({"threat": a.threat_id, "geography": sample.geography.model_dump(),
                           "indicator": sample.indicator, "value": selected.value if selected else None,
                           "unit": sample.unit, "case_definition": sample.case_definition,
                           "reporting_start": sample.reporting_period_start,
                           "reporting_cutoff": sample.reporting_period_end,
                           "publication_date": primary.publication_date, "retrieved_at": primary.retrieved_at,
                           "primary_source": primary.source_id if selected else None,
                           "source_url": str(primary.source_url), "confidence": g.confidence,
                           "selection_rationale": g.reason_codes, "conflicts": g.conflicts,
                           "source_agreement": g.quality_signals["source_agreement"],
                           "independent_authorities": sources,
                           "corroborating": [o.model_dump(mode="json") for o in all_candidates
                                            if selected and o.observation_id != selected.observation_id
                                            and o.value == selected.value
                                            and urlparse(str(o.source_url)).hostname != urlparse(str(selected.source_url)).hostname],
                           "evidence": [o.model_dump(mode="json") for o in all_candidates],
                           "evidence_ids": g.candidate_observation_ids,
                           "group_id": g.evidence_group_id, "status": g.status})
    return {"schema": schema, "metrics": output, "history": history,
            "filters": {"threat": threat, "region": region, "country": country, "period": period},
            "empty_message": "No verified observation available for this selection."}
