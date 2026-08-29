from backend.models.domain import Assessment, Observation

DEFAULT_INDICATORS = {
    "measles": "reported_measles_cases",
    "cholera": "reported_cholera_awd_cases",
    "ebola": "confirmed_cases",
}

SUPPORTED_METRICS = {
    "measles": {
        "signal": "reported_measles_cases",
        "reported_cases": "reported_measles_cases",
    },
    "cholera": {
        "signal": "reported_cholera_awd_cases",
        "reported_cases": "reported_cholera_awd_cases",
        "deaths": "reported_deaths",
        "cfr": "crude_cfr",
        "rate_per_100k": "cases_per_100k",
        "recent_change": "monthly_cases_change",
    },
    "ebola": {
        "signal": "confirmed_cases",
        "reported_cases": "confirmed_cases",
        "deaths": "reported_deaths",
        "cfr": "crude_cfr",
    },
}


def _latest(rows: list[Observation]) -> list[Observation]:
    latest: dict[tuple[str, str], Observation] = {}
    for row in rows:
        key = (row.geography.iso3 or row.geography.code or row.geography.name, row.indicator)
        current = latest.get(key)
        cutoff = row.reporting_period_end or row.event_date
        current_cutoff = current.reporting_period_end or current.event_date if current else None
        if current is None or (cutoff and (current_cutoff is None or cutoff > current_cutoff)):
            latest[key] = row
    return list(latest.values())


def build_map_data(
    assessments: list[Assessment], threat: str = "all", region: str = "Global", metric: str = "signal"
) -> dict:
    by_country: dict[str, dict] = {}
    coverage: dict[str, dict] = {}
    missing_coordinates: list[dict] = []
    available_metrics: dict[str, list[str]] = {}
    for assessment in assessments:
        disease = assessment.threat_id
        available_metrics[disease] = list(SUPPORTED_METRICS[disease])
        if threat != "all" and disease != threat:
            continue
        indicator = SUPPORTED_METRICS[disease].get(metric)
        if not indicator:
            continue
        rows = _latest(
            [
                row
                for row in assessment.observations
                if row.geography.level == "country" and row.indicator == indicator
            ]
        )
        if region != "Global":
            rows = [row for row in rows if row.geography.who_region == region]
        represented = {row.geography.iso3 or row.geography.name for row in rows}
        cutoff = max((row.reporting_period_end for row in rows if row.reporting_period_end), default=None)
        coverage[disease] = {
            "represented": len(represented),
            "unit": "reporting countries" if disease != "ebola" else "affected geographies",
            "reporting_cutoff": cutoff,
            "indicator": indicator,
        }
        for row in rows:
            geo = row.geography
            key = geo.iso3 or geo.code or geo.name
            signal = {
                "disease": disease,
                "country": geo.name,
                "source_country_name": geo.source_name or geo.name,
                "iso2": geo.iso2,
                "iso3": geo.iso3 or geo.code,
                "who_region": geo.who_region,
                "latitude": geo.latitude,
                "longitude": geo.longitude,
                "indicator": row.indicator,
                "value": row.value,
                "unit": row.unit,
                "reporting_cutoff": row.reporting_period_end,
                "publication_date": row.publication_date,
                "source": "World Health Organization",
                "source_id": row.source_id,
                "source_url": row.source_url,
                "evidence_id": row.observation_id,
                "confidence": assessment.evidence_confidence,
                "confidence_level": assessment.confidence_details.get("level", "UNSPECIFIED"),
                "limitation": assessment.limitations[0] if assessment.limitations else None,
            }
            if geo.latitude is None or geo.longitude is None:
                missing_coordinates.append(signal)
                continue
            country = by_country.setdefault(
                key,
                {
                    "country": geo.name,
                    "iso2": geo.iso2,
                    "iso3": geo.iso3 or geo.code,
                    "who_region": geo.who_region,
                    "latitude": geo.latitude,
                    "longitude": geo.longitude,
                    "signals": [],
                },
            )
            country["signals"].append(signal)
    return {
        "countries": list(by_country.values()),
        "coverage": coverage,
        "missing_coordinates": missing_coordinates,
        "available_metrics": available_metrics,
        "filters": {"threat": threat, "region": region, "metric": metric},
    }
