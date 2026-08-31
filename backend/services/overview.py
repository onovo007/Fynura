"""Cross-threat situation overview from canonical observations, not chart summaries."""
from backend.evidence import fuse_observations
from backend.models.domain import AskResponse


def threat_overview(assessments):
    facts, metrics, sources, evidence_ids, missing = [], [], {}, [], []
    indicators = {'ebola': 'confirmed_cases', 'measles': 'reported_measles_cases_global', 'cholera': 'reported_cholera_awd_cases'}
    labels = {'ebola': 'cumulative confirmed cases', 'measles': 'provisional monthly reported cases', 'cholera': 'reported cholera and acute watery diarrhoea cases'}
    for threat, item in assessments.items():
        if item is None:
            missing.append(threat.title())
            continue
        selected = {g.selected_observation_id for g in fuse_observations(item.observations)}
        rows = [o for o in item.observations if o.observation_id in selected and o.indicator == indicators[threat]
                and o.geography.name == item.geography.name]
        if not rows:
            missing.append(threat.title())
            continue
        o = max(rows, key=lambda row: str(row.reporting_period_end or row.event_date or ''))
        cutoff = str(o.reporting_period_end or o.event_date or 'not stated')
        period = f'{o.reporting_period_start} to {cutoff}' if o.reporting_period_start else f'through {cutoff}'
        facts.append(f'{threat.title()} ({o.geography.name}): {o.value:,.0f} {labels[threat]}, reporting {period}.')
        metrics.append({'label': f'{threat.title()} · {o.geography.name} · {cutoff}', 'value': o.value,
                        'unit': labels[threat], 'evidence_id': o.observation_id})
        evidence_ids.append(o.observation_id)
        sources[(str(o.source_url), cutoff)] = {'organization': 'World Health Organization', 'title': threat.title()+' surveillance',
            'url': str(o.source_url), 'reporting_cutoff': cutoff,
            'published': str(o.publication_date) if o.publication_date else None, 'retrieved_at': o.retrieved_at.isoformat()}
    if not facts:
        return AskResponse(answer='No resolved surveillance evidence is currently available for the monitored threats. Check source status before drawing conclusions.', evidence_ids=[], declined=True,
                           subject={'label': 'MONITORED HEALTH THREATS', 'geography': 'Available surveillance scopes'})
    answer = ('The health threats currently covered by Fynura are Ebola, measles and cholera. '
              'Here is the latest stored evidence for those threats, rather than only the previously selected chart.\n\n'
              + '\n\n'.join(facts)
              + '\n\nThese are different reporting periods and case definitions, not a ranking of the most dangerous disease. '
              'The reports do not establish today\'s case counts or every active health threat worldwide. '
              'Ask about a disease or country to inspect its evidence, trend or official control guidance.')
    if missing:
        answer += ' No resolved current snapshot is available for: '+', '.join(missing)+'.'
    return AskResponse(answer=answer, evidence_ids=evidence_ids, metrics=metrics, sources=list(sources.values()),
        subject={'label': 'MONITORED HEALTH THREATS', 'geography': 'Available surveillance scopes'},
        limitations=['Coverage is limited to the three monitored threats, not a comprehensive global threat assessment.',
                     'Reporting dates differ. Latest stored does not mean real-time; counts must not be summed or used alone to rank risk.'])
