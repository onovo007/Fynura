from backend.models.domain import AskRequest, AskResponse
from backend.services.briefs import create_brief, wants_brief
from backend.services.history import historical_answer


def test_brief_request_detection():
    assert wants_brief('Create an infographic about cholera')
    assert wants_brief('Write a report brief for a journalist')
    assert not wants_brief('What are the reported cases?')


def test_unsupported_answers_do_not_create_surveillance_graphics():
    request = AskRequest(question='Create a report about something unsupported')
    assert create_brief(request, AskResponse(answer='No evidence', evidence_ids=[], declined=True)) is None


def test_historical_brief_reuses_total_and_evidence_ids():
    request = AskRequest(question='Create a report brief about annual cholera in Nigeria from 2017 to 2024 via OWID')
    answer = historical_answer(request)
    assert answer.subject['geography'] == 'Nigeria'
    brief = create_brief(request, answer)
    assert brief['metrics'][0]['value'] > 0
    assert set(answer.evidence_ids) <= set(brief['evidence_ids'])
    assert brief['sources'][0]['organization'] == 'WHO via Our World in Data'
    assert any('not automatically additive' in s for s in brief['limitations'])


def test_ask_route_returns_brief_and_does_not_change_plain_answers():
    from backend.main import ask
    request = AskRequest(question='Create an infographic about measles in the United States in 2019')
    response = ask(request)
    assert response.brief and len(response.brief['evidence_ids']) >= 12
    plain = ask(AskRequest(question='Measles in the United States in 2019?'))
    assert plain.brief is None


def test_niger_and_nigeria_are_distinct():
    for country in ('Niger', 'Nigeria'):
        answer = historical_answer(AskRequest(question=f'Create a report about annual cholera in {country} in 2024 via OWID'))
        assert answer.subject['geography'] == country


def test_historical_brief_explains_control_and_risk_without_inventing_demographics():
    request = AskRequest(question='Create a report about annual cholera in Nigeria in 2024 via OWID')
    brief = create_brief(request, historical_answer(request))
    assert len(brief['actions']) == 3
    assert any(s['title'] == 'WHO control priorities' for s in brief['sections'])
    assert any('not a claim' in s['text'] for s in brief['sections'])
    assert not brief['ranking']
    assert any(s['url'].endswith('/cholera') for s in brief['sources'])


def test_guidance_is_disease_specific_and_unknown_diseases_have_none():
    from backend.services.brief_guidance import guidance_sections
    for threat in ('cholera', 'measles', 'ebola'):
        sections, actions, sources = guidance_sections(threat)
        assert len(actions) == 3 and len(sections) == 3
        assert sources[0]['reviewed_on'] == '2026-08-30'
    assert guidance_sections('unknown') == ([], [], [])
    assert 'virus' in guidance_sections('ebola')[1][-1]['text']
