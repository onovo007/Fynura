"""Shared, request-scoped intelligence orchestration for typed and streamed chat."""
import asyncio
import logging
import random
from contextlib import aclosing
from google.genai.errors import APIError
from typing import Literal
from pydantic import BaseModel
from backend.models.domain import ContextEnvelope
from backend.services.query_router import Route, route_question, REFUSAL, SCOPE, VERSION
from backend.services.research_chat import run_text_agent, INSTRUCTION


class Classification(BaseModel):
    mode: Literal['knowledge', 'research', 'surveillance', 'scope', 'safety']
    domain: str
    threat: Literal['measles', 'ebola', 'cholera'] | None = None


async def classify(request):
    result = await run_text_agent('fynura_intent', INSTRUCTION + '''
Classify the user's current request, do not answer it. Use recent conversation only
to resolve genuine follow-ups. Never let prior topics override a new question.
knowledge: established public-health/scientific concepts, methods, capacity building.
research: current external facts, recommendations or developments requiring sources.
surveillance: latest stored figures for one of the three monitored diseases.
scope: unrelated safe questions. safety: requests for operational biological harm,
concealing transmission, falsifying surveillance, or individual diagnosis/treatment.
Legitimate sexual health, HIV and epidemiological questions are in scope.
Return only the classification schema. Select a threat only when actually relevant.
''', {'question':request.question, 'conversation':[t.model_dump() for t in request.history]}, Classification)
    parsed = Classification.model_validate_json(result)
    context = ContextEnvelope(threat_id=parsed.threat, disease=parsed.threat) if parsed.threat else None
    return Route('SEMANTIC_' + parsed.mode.upper(), parsed.mode, parsed.domain, parsed.threat, context)


def envelope(answer, mode, **kwargs):
    return dict(answer=answer, sources=[], supports=[], evidence_ids=[], suggestions='',
                mode=mode, router_version=VERSION, **kwargs)


def canonical(answer):
    data = answer.model_dump(mode='json')
    data.update(mode='VERIFIED SURVEILLANCE' if data['evidence_ids'] else 'EVIDENCE AVAILABILITY',
                supports=[], suggestions='', router_version=VERSION,
                evidence_status='Stored source-reported evidence. Use the reporting cutoff, not the retrieval date, to judge recency.')
    data['sources'] = [{**s, 'id':i+1, 'title':s.get('title') or s.get('organization') or s.get('source_id') or 'Source',
                        'url':s.get('url') or s.get('source_url')} for i,s in enumerate(data['sources'])]
    return data


def registry_answer(status):
    listing = '\n'.join(f"• {s['name']}: {s['status'].lower()}." for s in status['network'])
    return envelope(f"Fynura monitors measles, Ebola and cholera with {status['verified_snapshots']} available surveillance snapshots. Its source registry contains {len(status['network'])} source families:\n{listing}\nOWID supplies WHO-derived historical context, not independent WHO corroboration. Configured or candidate sources are not operational feeds. Scientific research can consult additional sources without adding a structured surveillance feed.",
                    'SOURCE REGISTRY', evidence_support='APPLICATION STATE', evidence_status='Current application registry and snapshot availability.')


def signal_answer(request):
    from backend.services.early_history import early_history
    country = (request.context.visual_context or {}).get('country') if request.context else None
    if not country:
        return envelope('Select a country in Early signal detection and use “Ask about this signal” to interpret its computed result.', 'SIGNAL REVIEW')
    result = early_history(country)
    if not result['ready']:
        return envelope(f"{result['geography']}: {result['status']}. {result['note']}", 'SIGNAL REVIEW')
    latest = result['points'][-1]
    answer = (f"For {result['geography']}, the exploratory measles CUSUM is {latest['cusum']:.3f} through {result['reporting_cutoff']}, compared with threshold {result['threshold']}. "
              f"{result['status']}. The latest month has {latest['value']:,.0f} reported cases versus a seasonal baseline expectation of {latest['expected']:,.2f}. "
              f"The baseline contains 60 monthly observations from {result['baseline_start']} to {result['baseline_end']}; 12 subsequent months are monitored with k={result['k']}. "
              f"{result['note']} Review reporting completeness and outbreak-specific evidence before acting. This is not a forecast.")
    data = envelope(answer, 'SIGNAL REVIEW', evidence_status=result['method'], signal=result)
    data['evidence_ids'] = result['baseline_evidence_ids'] + [p['evidence_id'] for p in result['points']]
    data['sources'] = [{'id':1, 'title':result['source'], 'url':result['source_url']}]
    return data


REQUEST_TIMEOUT_SECONDS = 250
MAX_ATTEMPTS = 3
logger = logging.getLogger(__name__)


async def intelligence_events(request, answer_fn, status_fn, research_fn):
    """Retry transient provider failures only, before delivering an answer.

    One deadline includes classification, research, cleanup and backoff. Both
    public chat endpoints share this policy; no client POST is replayed.
    """
    async with asyncio.timeout(REQUEST_TIMEOUT_SECONDS):
        for attempt in range(1, MAX_ATTEMPTS + 1):
            delivered = False
            try:
                async with aclosing(_intelligence_once(request, answer_fn, status_fn, research_fn)) as events:
                    async for event in events:
                        if event['type'] == 'answer':
                            delivered = True
                        yield event
                if attempt > 1:
                    logger.warning('fynura_provider_recovery attempts=%s', attempt)
                return
            except APIError as error:
                if delivered or error.code not in {429, 500, 502, 503, 504} or attempt == MAX_ATTEMPTS:
                    raise
                delay = 2 ** attempt + random.uniform(0, 1)
                logger.warning('fynura_provider_retry code=%s next_attempt=%s', error.code, attempt + 1)
                yield {'type': 'status', 'message':
                       f'The AI service is temporarily busy or unavailable. Retrying automatically ({attempt + 1} of {MAX_ATTEMPTS})…'}
                await asyncio.sleep(delay)


async def _intelligence_once(request, answer_fn, status_fn, research_fn):
    route = route_question(request)
    if route.mode == 'classify':
        yield {'type':'status', 'message':'Understanding your question and relevant conversation…'}
        route = await classify(request)
    if route.mode in {'safety', 'scope'}:
        yield {'type':'answer', 'data':envelope(route.reason or (REFUSAL if route.mode == 'safety' else SCOPE),
                                               'SAFETY GUIDANCE' if route.mode == 'safety' else 'FYNURA SCOPE', declined=True)}
        return
    if route.mode == 'registry':
        if route.intent == 'PRODUCT_SCOPE':
            yield {'type':'answer','data':envelope('Fynura currently monitors measles, Ebola and cholera with structured surveillance. Ask Fynura also supports broader public-health science and methods; that does not mean additional diseases have operational surveillance feeds.', 'MONITORED THREATS', evidence_support='APPLICATION STATE')}
            return
        yield {'type':'answer','data':registry_answer(await asyncio.to_thread(status_fn))}
        return
    resolved = request.model_copy(update={'context':route.context, 'threat_id':route.threat})
    if route.mode == 'signal':
        yield {'type':'answer','data':await asyncio.to_thread(signal_answer, resolved)}
        return
    if route.mode == 'surveillance':
        yield {'type':'status','message':'Checking the reporting scope and linked surveillance evidence…'}
        result = await asyncio.to_thread(answer_fn, resolved)
        yield {'type':'answer','data':canonical(result)}
        return
    stored = {}
    if route.mode == 'hybrid':
        stored = (await asyncio.to_thread(answer_fn, resolved)).model_dump(mode='json')
    # Scientific questions never enter the dashboard-answer fallback. All modes
    # use the same provider safety instructions, bounded history and citations.
    async for event in research_fn(resolved, stored, mode=route.mode, domain=route.domain):
        if event['type'] == 'answer':
            event['data'].setdefault('mode', 'EVIDENCE AND INTERPRETATION' if route.mode == 'hybrid' else 'LIVE RESEARCH')
            event['data']['router_version'] = VERSION
            if route.mode == 'hybrid':
                from backend.models.domain import AskResponse
                event['data']['surveillance'] = canonical(AskResponse.model_validate(stored))
                event['data']['surveillance']['brief'] = None
                if stored.get('brief'):
                    event['data']['brief'] = stored['brief']
        yield event
