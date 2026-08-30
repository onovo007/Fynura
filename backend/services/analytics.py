from datetime import UTC, datetime

from backend.epidemiology.cusum import detect
from backend.epidemiology.metrics import crude_cfr


def intelligence_snapshot(assessment):
    rows = [o for o in assessment.observations if o.geography.name == assessment.geography.name]
    cases = [o for o in rows if o.indicator in {'confirmed_cases', 'reported_cholera_awd_cases', 'reported_measles_cases_global'}]
    cases.sort(key=lambda o: o.reporting_period_end or o.retrieved_at.date())
    if not cases:
        return None
    latest = cases[-1]
    deaths = next((o for o in rows if o.indicator == 'reported_deaths' and o.reporting_period_end == latest.reporting_period_end), None)
    cfr = crude_cfr(deaths, latest) if deaths else None
    prior = cases[-2] if len(cases) > 1 else None
    compatible = prior and prior.case_definition == latest.case_definition and prior.unit == latest.unit
    return {'threat': assessment.threat_id, 'geography': latest.geography.name,
            'cases': latest.value, 'deaths': deaths.value if deaths else None,
            'cfr': cfr.value if cfr else None, 'cfr_label': 'Fynura-computed crude CFR',
            'ifr': None, 'ifr_reason': 'Not estimable from current surveillance data. IFR requires total infections, not only reported cases.',
            'change': latest.value-prior.value if compatible else None,
            'percent_change': (latest.value-prior.value)/prior.value*100 if compatible and prior.value else None,
            'reporting_cutoff': latest.reporting_period_end,
            'reporting_lag_days': (datetime.now(UTC).date()-latest.reporting_period_end).days if latest.reporting_period_end else None,
            'confidence': assessment.confidence_details, 'evidence_ids': [latest.observation_id]+([deaths.observation_id] if deaths else []),
            'source_url': str(latest.source_url), 'assessment_id': assessment.assessment_id,
            'early_signal': detect([{'date': str(o.reporting_period_end), 'value': o.value,
                                    'threat': o.threat_id, 'geography': o.geography.name,
                                    'indicator': o.indicator, 'unit': o.unit, 'case_definition': o.case_definition,
                                    'evidence_ids': [o.observation_id]} for o in cases], frequency='monthly', seasonal=True)}
