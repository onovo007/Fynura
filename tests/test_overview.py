from backend.models.domain import AskRequest, ContextEnvelope
from backend.services.context import is_threat_overview, resolve_context
from backend.services.overview import threat_overview


def test_broad_question_overrides_chart_and_history_contexts():
    for question in ('whats teh current health threat?', 'What are the current health threats?', 'Which outbreaks are you monitoring?', 'Give me an overview of active threats'):
        assert is_threat_overview(question)
        for visual in ('historical_archive', 'shared_workspace', 'trajectory'):
            request = AskRequest(question=question, threat_id='measles', context=ContextEnvelope(threat_id='measles', visual=visual))
            assert resolve_context(request) == (None, None)


def test_explicit_disease_and_deictic_followups_retain_context():
    for question in ('What changed?', "What's happening?", 'What is the current measles situation?', 'What does this health threat mean?'):
        assert not is_threat_overview(question)
        request = AskRequest(question=question, context=ContextEnvelope(threat_id='measles'))
        assert resolve_context(request)[0] == 'measles'


def test_empty_overview_does_not_invent_current_threat_evidence():
    response = threat_overview({'measles': None, 'ebola': None, 'cholera': None})
    assert response.declined and not response.evidence_ids


def test_overview_has_traceable_dates_and_does_not_use_canned_summaries(monkeypatch):
    from datetime import date, datetime, UTC
    from backend.models.domain import Assessment, Geography, Observation
    from backend.main import answer_question, repo
    items = {}
    for disease, indicator in [('measles','reported_measles_cases_global'),('cholera','reported_cholera_awd_cases'),('ebola','confirmed_cases')]:
        geography = Geography(name='DRC' if disease == 'ebola' else 'Global', level='country' if disease == 'ebola' else 'global')
        row = Observation(threat_id=disease, indicator=indicator, value=100, unit='cases', geography=geography,
            reporting_period_end=date(2026,6,30), source_id='who_'+disease, source_url='https://www.who.int/'+disease,
            source_type='international_health_authority', extraction_method='fixture', extraction_confidence=.99,
            supporting_excerpt='fixture',run_id='fixture')
        items[disease] = Assessment(run_id='fixture', threat_id=disease, geography=geography,
            evidence_cutoff=datetime.now(UTC), headline='fixture', summary='DO NOT COPY THIS CANNED SUMMARY',
            claims=[],observations=[row],evidence_groups=[],evidence_confidence=.99,limitations=[],freshness='cached')
    monkeypatch.setattr(repo, 'latest_assessment', lambda disease: items.get(disease))
    response = answer_question(AskRequest(question='whats teh current health threat?', context=ContextEnvelope(threat_id='measles',visual='historical_archive')))
    assert len(response.metrics) == len(response.sources) == len(response.evidence_ids) == 3
    assert '2026-06-30' in response.answer and 'DO NOT COPY' not in response.answer
    assert "today's case counts" in response.answer
    assert response.subject['label'] == 'MONITORED HEALTH THREATS'
