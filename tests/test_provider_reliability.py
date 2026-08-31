import asyncio

import pytest
from google.genai.errors import ClientError, ServerError
from google.adk.models.google_llm import _ResourceExhaustedError
from backend.services import intelligence as module


def capacity():
    return _ResourceExhaustedError(ClientError(429, {'error': {'message': 'private provider details'}}))


def collect():
    async def run():
        return [event async for event in module.intelligence_events(None, None, None, None)]
    return asyncio.run(run())


@pytest.mark.parametrize('error', [capacity(), ServerError(503, {})])
def test_transient_retry_succeeds_with_visible_safe_feedback(monkeypatch, error):
    calls, delays = [], []

    async def once(*args):
        calls.append(1)
        if len(calls) == 1:
            raise error
        yield {'type': 'answer', 'data': {'answer': 'Verified response'}}

    async def sleep(delay):
        delays.append(delay)

    monkeypatch.setattr(module, '_intelligence_once', once)
    monkeypatch.setattr(module.asyncio, 'sleep', sleep)
    events = collect()
    assert len(calls) == 2 and 2 <= delays[0] <= 3
    assert 'Retrying automatically (2 of 3)' in events[0]['message']
    assert 'private' not in str(events)
    assert sum(e['type'] == 'answer' for e in events) == 1


def test_persistent_capacity_is_bounded(monkeypatch):
    calls, delays = [], []

    async def once(*args):
        calls.append(1)
        raise capacity()
        yield

    async def sleep(delay):
        delays.append(delay)

    monkeypatch.setattr(module, '_intelligence_once', once)
    monkeypatch.setattr(module.asyncio, 'sleep', sleep)
    with pytest.raises(ClientError):
        collect()
    assert len(calls) == 3 and len(delays) == 2
    assert 4 <= delays[1] <= 5


@pytest.mark.parametrize('error', [ClientError(400, {}), ClientError(401, {}),
                                 ClientError(403, {}), RuntimeError('private'),
                                 ValueError('invalid'), asyncio.CancelledError()])
def test_nontransient_and_cancellation_never_retry(monkeypatch, error):
    calls = []

    async def once(*args):
        calls.append(1)
        raise error
        yield

    monkeypatch.setattr(module, '_intelligence_once', once)
    with pytest.raises(type(error)):
        collect()
    assert len(calls) == 1


def test_never_replay_after_answer(monkeypatch):
    calls = []

    async def once(*args):
        calls.append(1)
        yield {'type': 'answer', 'data': {}}
        raise capacity()

    monkeypatch.setattr(module, '_intelligence_once', once)
    with pytest.raises(ClientError):
        collect()
    assert len(calls) == 1


def test_total_deadline_cancels_and_closes_generator(monkeypatch):
    closed = []

    async def once(*args):
        try:
            await asyncio.Event().wait()
            yield
        finally:
            closed.append(True)

    monkeypatch.setattr(module, '_intelligence_once', once)
    monkeypatch.setattr(module, 'REQUEST_TIMEOUT_SECONDS', .01)
    with pytest.raises(TimeoutError):
        collect()
    assert closed == [True]


def test_classifier_capacity_also_recovers(monkeypatch):
    from backend.services.query_router import Route
    from backend.services.research_chat import ResearchRequest
    calls = []

    async def classify(request):
        calls.append(1)
        if len(calls) == 1:
            raise capacity()
        return Route('TEST', 'scope', 'Public health', None, None)

    async def sleep(delay):
        pass

    monkeypatch.setattr(module, 'route_question', lambda r: Route('TEST', 'classify', 'Public health', None, None))
    monkeypatch.setattr(module, 'classify', classify)
    monkeypatch.setattr(module.asyncio, 'sleep', sleep)

    async def run():
        return [e async for e in module.intelligence_events(ResearchRequest(question='Hello'), None, None, None)]

    events = asyncio.run(run())
    assert len(calls) == 2
    assert events[-1]['type'] == 'answer'
