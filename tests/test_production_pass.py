from datetime import date, timedelta

from fastapi.testclient import TestClient

from backend.epidemiology.cusum import detect
from backend.main import app
from backend.models.domain import AskRequest
from backend.services.context import resolve_context


def series(values):
    return [{'date': str(date(2020, 1, 1)+timedelta(weeks=i)), 'value': value,
             'threat': 'fixture', 'geography': 'Example', 'indicator': 'weekly_cases',
             'case_definition': 'confirmed', 'unit': 'persons', 'evidence_ids': [str(i)]}
            for i, value in enumerate(values)]


def test_explicit_questions_override_all_stale_contexts():
    for stale in ('ebola', 'cholera', 'measles'):
        for explicit in ('ebola', 'cholera', 'measles'):
            threat, context = resolve_context(AskRequest(question=f'What changed in {explicit}?', context={
                'threat_id': stale, 'disease': stale, 'geography': 'Old country', 'reporting_cutoff': '2020-01-01'}))
            assert threat == explicit
            if stale != explicit:
                assert context.geography == 'Global'
                assert context.reporting_cutoff is None


def test_cusum_normal_spike_and_sustained_elevation():
    baseline = [9, 11]*13
    assert detect(series(baseline+[10]*5))['signal'] == 'NO STATISTICAL SIGNAL'
    assert detect(series(baseline+[12,10,10,10]))['signal'] == 'NO STATISTICAL SIGNAL'
    elevated = detect(series(baseline+[13]*8))
    assert elevated['signal'] == 'STRONG SIGNAL'
    assert elevated['points'][-1]['evidence_ids']


def test_cusum_withholds_ineligible_results():
    assert detect(series([1,2,3]))['eligibility'] == 'NOT ELIGIBLE'
    rows = series([9,11]*16)
    for output in (detect(rows[:4]+rows[5:]), detect(rows, revised=True),
                   detect(rows, structural_break=True)):
        assert output['eligibility'] == 'NOT ELIGIBLE'
        assert output['points'] == []
    assert detect(rows, seasonal=True)['eligibility'] == 'LIMITED'
    rows[0]['value'] = None
    assert detect(rows)['eligibility'] == 'NOT ELIGIBLE'


def test_internal_refresh_requires_verified_identity():
    assert TestClient(app).post('/internal/refresh').status_code == 403
    assert TestClient(app).get('/api/admin/source-health').status_code in (401, 403)


def test_all_supported_map_intersections_preserve_country_membership():
    from backend.models.domain import Geography
    from backend.services.map_data import SUPPORTED_METRICS, build_map_data
    from tests.test_map_data import assessment, observation
    regions = ['Africa', 'Americas', 'Europe', 'Eastern Mediterranean', 'South-East Asia', 'Western Pacific']
    samples = []
    for threat, metrics in SUPPORTED_METRICS.items():
        rows = [observation(threat, indicator, 20, Geography(name=region, level='country', iso3=str(i), who_region=region, latitude=i, longitude=i))
                for i, region in enumerate(regions) for indicator in set(metrics.values())]
        samples.append(assessment(threat, rows))
    for threat in ['all', *SUPPORTED_METRICS]:
        for region in ['Global', *regions]:
            for metric in {m for metrics in SUPPORTED_METRICS.values() for m in metrics}:
                data = build_map_data(samples, threat, region, metric)
                assert len(data['countries']) == (6 if region == 'Global' else 1) if any(metric in SUPPORTED_METRICS[t] for t in SUPPORTED_METRICS if threat in ('all', t)) else not data['countries']
                assert all(region == 'Global' or c['who_region'] == region for c in data['countries'])


def test_failed_refresh_retains_snapshot_and_respects_backoff():
    import asyncio

    from backend.repositories.memory import MemoryRepository
    from backend.services.refresh import RefreshService
    repository = MemoryRepository()
    class Failure:
        calls = 0
        async def assess_ebola(self):
            self.calls += 1
            raise ValueError('Source unavailable')
    pipeline = Failure()
    service = RefreshService(repository, pipeline)
    asyncio.run(service.refresh('ebola'))
    asyncio.run(service.refresh('ebola'))
    assert pipeline.calls == 1
    assert service.status('ebola')['next_scheduled_check']
