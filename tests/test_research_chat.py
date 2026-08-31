from types import SimpleNamespace
import asyncio
import pytest
from pydantic import ValidationError
from backend.services.research_chat import ResearchRequest, grounded_result, INSTRUCTION


def metadata(data):
    return SimpleNamespace(model_dump=lambda **kwargs: data)


def test_missing_grounding_does_not_present_model_text_as_current_fact():
    result = grounded_result('Invented current count 999', None, 'test')
    assert '999' not in result['answer']
    assert result['sources'] == []


def test_only_provider_https_sources_and_matching_supports_are_exposed():
    result = grounded_result('Reported counts.', metadata({
        'grounding_chunks': [{'web': {'uri':'javascript:alert(1)', 'title':'bad'}},
                             {'web': {'uri':'https://www.who.int/test', 'title':'WHO'}}],
        'grounding_supports': [{'segment':{'text':'Reported counts.'}, 'grounding_chunk_indices':[0,1,10]}],
        'search_entry_point': {'rendered_content':'<div>Google suggestions</div>'},
    }), 'test')
    assert len(result['sources']) == 1
    assert result['supports'][0]['sources'] == [2]
    assert result['suggestions']
    assert 'independent corroboration is not automatically' in result['evidence_status']


def test_conversation_and_question_are_bounded():
    with pytest.raises(ValidationError):
        ResearchRequest(question='x'*1001)
    with pytest.raises(ValidationError):
        ResearchRequest(question='test question', history=[{'question':'x','answer':'y'}]*9)
    assert ResearchRequest(question='Current health threats?').context is None


def test_prompt_requires_freshness_demographic_evidence_and_independence():
    for phrase in ['NOT limited', 'Age/sex/occupation', 'not independent confirmation',
                   'Never add overlapping cumulative reports', 'not a dashboard template']:
        assert phrase in INSTRUCTION


def test_stream_endpoint_mocked_success_and_error(monkeypatch):
    from fastapi.testclient import TestClient
    import backend.main as main
    from backend.models.domain import AskResponse
    monkeypatch.setattr(main.settings, 'fynura_onboarding_required', False)
    monkeypatch.setattr(main, 'answer_question', lambda request: AskResponse(answer='Stored',evidence_ids=[]))
    async def fake(request, stored, **kwargs):
        assert stored == {}
        yield {'type':'answer','data':{'answer':'Research'}}
    monkeypatch.setattr(main, 'research_events', fake)
    client=TestClient(main.app)
    response=client.post('/api/chat/stream',json={'question':'Current threats?'})
    assert response.status_code == 200
    assert 'Research' in response.text
    async def fail(request, stored, **kwargs):
        raise RuntimeError('private provider details')
        yield
    monkeypatch.setattr(main, 'research_events', fail)
    response=client.post('/api/chat/stream',json={'question':'Current threats?'})
    assert 'private provider details' not in response.text
    assert 'No cached answer' in response.text
