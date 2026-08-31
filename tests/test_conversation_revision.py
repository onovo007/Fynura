import asyncio
from backend.services.science import science_answer
from backend.services.research_chat import ResearchRequest, research_events, INSTRUCTION
from backend.services.research_chat import grounded_result

def test_typo_definition_is_not_chart_response():
    answer=science_answer('what is heard immunity?')
    assert 'Herd immunity' in answer and 'Ebola' not in answer
    assert len(answer.split())<100

def test_definition_shared_route_ignores_irrelevant_visual():
    from backend.services.intelligence import intelligence_events
    async def fake(request, stored, **kwargs):
        assert request.context is None and request.threat_id is None
        assert stored == {} and kwargs['mode'] == 'knowledge'
        yield {'type':'answer','data':{'answer':'Scientific explanation', 'sources':[]}}
    def forbidden(*args):
        raise AssertionError('A scientific question must not query dashboard evidence')
    async def run():
        request=ResearchRequest(question='what is herd immunity?',threat_id='ebola')
        return [event async for event in intelligence_events(request, forbidden, forbidden, fake)]
    result=asyncio.run(run())[0]['data']
    assert 'Ebola' not in result['answer']

def test_conversation_bounds_and_concise_instruction():
    request=ResearchRequest(question='Does that apply to measles?',history=[{'question':'Herd immunity?', 'answer':'Community protection.'}]*8)
    assert len(request.history)==8
    assert '80-180 words' in INSTRUCTION

def test_missing_sources_message_does_not_assume_outbreak_question():
    result = grounded_result('An unsupported answer', None, 'test')
    assert not result['sources']
    assert 'outbreak' not in result['answer']
    assert 'verify supporting sources' in result['answer']
