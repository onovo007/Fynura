"""Source-grounded, reproducible briefing payloads. No invented totals or imagery."""
import re
from datetime import UTC, datetime

from backend.evidence import fuse_observations
from backend.services.history import catalog, historical_series
from backend.services.brief_guidance import guidance_sections


def wants_brief(question):
    return bool(re.search(r'\b(briefs?|briefings?|reports?|infographics?|info graphics?)\b', question, re.IGNORECASE))


def create_brief(request, answer, latest_assessment=None):
    if answer.declined or not answer.evidence_ids or not answer.sources:
        return None
    historical = answer.subject.get('label') == 'HISTORICAL EVIDENCE'
    metrics = list(answer.metrics)
    sources = [dict(s) for s in answer.sources]
    evidence_ids = list(answer.evidence_ids)
    context = request.context
    scope = (context.visual_context or {}) if context else {}
    timeline = []
    historical_data = None
    if historical:
        # Match the source actually used in the answer, not a guessed dataset.
        key = next((k for k, d in catalog()['datasets'].items() if d['source_url'] == sources[0]['url']), None)
        if key:
            country = next((c for c in catalog()['datasets'][key]['countries'] if c['name'] == answer.subject.get('geography')), None)
            years = [int(y) for y in re.findall(r'\b(?:19|20)\d{2}\b', request.question)]
            start, end = (min(years), max(years)) if years else (scope.get('start', 2010), scope.get('end', 2026))
            if country:
                historical_data = historical_series(key, country['code'], int(start), int(end))
                summary = historical_data['summary']
                if summary.get('total') is not None:
                    metrics = [{'label': summary['label'], 'value': summary['total'], 'unit': 'reported cases'},
                        {'label': 'Reporting periods available', 'value': summary['count'], 'unit': f"of {summary['expected']} requested"}]
                    if summary.get('peak'):
                        metrics.append({'label': 'Peak period: '+summary['peak']['period'], 'value': summary['peak']['value'], 'unit': 'reported cases'})
                    evidence_ids = list(dict.fromkeys(evidence_ids + summary['evidence_ids']))
                timeline.append({'title': 'Historical record', 'text': f"{historical_data['title']}. Selected years {start} to {end}. {historical_data['limitations']}", 'source_url': sources[0]['url']})
    if historical_data and latest_assessment:
        # Select only matching geography. ALL historical Ebola is not comparable to one current country.
        code = historical_data['country']
        indicators = {'reported_measles_cases', 'reported_cholera_awd_cases', 'confirmed_cases'}
        selected = {g.selected_observation_id for g in fuse_observations(latest_assessment.observations)}
        rows = [o for o in latest_assessment.observations if o.geography.iso3 == code and o.indicator in indicators and o.observation_id in selected]
        if rows:
            latest = max(rows, key=lambda o: str(o.reporting_period_end or o.event_date))
            cutoff = str(latest.reporting_period_end or latest.event_date)
            indicator_label = {'reported_cholera_awd_cases': 'reported cholera and acute watery diarrhoea cases', 'reported_measles_cases': 'reported measles cases', 'confirmed_cases': 'confirmed cases'}[latest.indicator]
            text = f"{latest.geography.name}: {latest.value:,.0f} {latest.unit}, {indicator_label}, reporting through {cutoff}. This is a separate current observation, not an amount added to the historical sum."
            timeline.append({'title': 'Latest stored report for this country', 'text': text, 'source_url': str(latest.source_url)})
            sources.append({'organization': 'World Health Organization', 'title': 'Latest stored country observation', 'url': str(latest.source_url), 'reporting_cutoff': cutoff, 'published': str(latest.publication_date) if latest.publication_date else None, 'retrieved_at': latest.retrieved_at.isoformat()})
            evidence_ids.append(latest.observation_id)
        else:
            timeline.append({'title': 'Latest report connection', 'text': 'No compatible latest country observation is stored for this historical scope. No combined inception-to-present total is asserted.'})
    threat = next((t for t in ('cholera', 'measles', 'ebola') if t in request.question.lower()), None)
    threat = threat or (latest_assessment.threat_id if latest_assessment else request.threat_id)
    if not threat and context:
        threat = context.threat_id or context.disease
    sections, actions, guidance_sources = guidance_sections(threat)
    sources.extend(guidance_sources)
    sections.insert(0, {'title': 'Affected groups in this evidence', 'text': 'The selected structured evidence does not establish an age, sex or occupation breakdown. The risk groups below are general WHO background, not a claim about who accounts for most cases in this outbreak.', 'kind': 'Evidence gap'})
    ranking = []
    if latest_assessment and not historical and answer.subject.get('geography', 'Global').lower() == 'global':
        selected = {g.selected_observation_id for g in fuse_observations(latest_assessment.observations)}
        groups = {}
        for o in latest_assessment.observations:
            if o.observation_id not in selected or o.geography.level != 'country' or o.indicator not in {'reported_measles_cases', 'reported_cholera_awd_cases', 'confirmed_cases'}:
                continue
            family = (str(o.reporting_period_end), str(o.reporting_period_start), o.indicator, o.unit, o.case_definition, str(o.source_url))
            groups.setdefault(family, []).append(o)
        if groups:
            family, rows = max(groups.items(), key=lambda pair: (pair[0][0], len(pair[1])))
            rows = sorted(rows, key=lambda o: o.value, reverse=True)
            ranking = [{'label': o.geography.name, 'value': o.value, 'unit': o.unit, 'evidence_id': o.observation_id, 'source_url': str(o.source_url)} for o in rows[:5]]
            evidence_ids.extend(o.observation_id for o in rows[:5])
            sections.insert(0, {'title': 'Where reported burden is greatest', 'text': '; '.join(f'{o.geography.name}: {o.value:,.0f} {o.unit}' for o in rows[:5])+f'. Among {len(rows)} comparable stored country reports through {family[0]}. This is reported volume, not population-adjusted risk or a complete global ranking.', 'kind': 'Calculated from comparable surveillance observations', 'source_url': family[-1]})
    if not ranking:
        sections.insert(0, {'title': 'Geographic interpretation', 'text': 'This brief describes '+answer.subject.get('geography', 'the selected scope')+'. The selected evidence does not establish a comparable within-country hotspot ranking. A national total cannot locate transmission within a country.', 'kind': 'Selected scope'})
    caveats = list(answer.limitations)
    if historical:
        caveats.append('Historical annual records, monthly reports and cumulative outbreak updates are not automatically additive. Overlapping periods, gaps or different case definitions prevent a defensible combined total.')
    caveats.append('A generated evidence brief, not an official health-authority report or personal medical advice. Check original sources before publication.')
    topic = historical_data['title'] if historical_data else answer.subject.get('label', 'Selected evidence')
    return {'title': f"Fynura evidence brief: {topic} | {answer.subject.get('geography', 'Selected scope')}",
        'generated_at': datetime.now(UTC).isoformat(), 'audience': request.stakeholder_mode,
        'question': request.question, 'scope': dict(answer.subject), 'summary': answer.answer,
        'metrics': metrics[:6], 'timeline': timeline, 'what_changed': answer.what_changed,
        'sections': sections, 'actions': actions, 'ranking': ranking,
        'limitations': list(dict.fromkeys(caveats)), 'sources': sources,
        'evidence_ids': list(dict.fromkeys(evidence_ids)),
        'method': 'Deterministic formatting of retrieved evidence; no new epidemiological claims generated.'}
