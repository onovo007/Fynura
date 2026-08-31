from fastapi.testclient import TestClient

from backend.main import app
from backend.models.domain import AskRequest
from backend.services.history import historical_answer, historical_series, history_metadata
from backend.sources.historical_catalog import cholera_history, ebola_chronology


def test_packaged_history_has_real_coverage_and_keeps_frequencies_separate():
    meta = history_metadata()
    assert meta['measles']['first'] == '2012-01'
    assert meta['cholera']['frequency'] == 'annual'
    assert meta['ebola']['frequency'] == 'outbreak'
    rows = historical_series('measles', 'USA', 2019, 2019)['points']
    assert len(rows) == 12
    assert all(p['evidence_id'] for p in rows)


def test_historical_questions_keep_dates_country_and_provenance():
    result = historical_answer(AskRequest(question='What happened with measles in the United States in 2019?'))
    assert result.evidence_ids and '2019' in result.answer
    assert result.sources[0]['organization'] == 'WHO'
    assert historical_answer(AskRequest(question='What is the latest cholera situation?')) is None
    assert historical_answer(AskRequest(question='Measles in 2010 in the United States?')).declined
    assert historical_answer(AskRequest(question='Measles in 2015?')).declined


def test_history_api_validates_and_does_not_invent_missing_years():
    client = TestClient(app)
    assert client.get('/api/history').status_code == 200
    assert client.get('/api/history/measles?country=UNKNOWN').status_code == 422
    assert client.get('/api/history/measles?country=USA&start=2020&end=2010').status_code == 422
    assert client.get('/api/history/cholera?country=NGA&start=2025&end=2025').json()['points'] == []


def test_ebola_parser_skips_ambiguous_counts_and_keeps_outbreaks_separate():
    html = '<main><h3>2014</h3><h4>A</h4><p>Species: Example</p><p>Reported number of cases: 20</p><p>Reported deaths: 8</p><h4>B</h4><p>Reported number of cases: 1 2 confirmed; 2 probable</p></main>'
    rows, skipped = ebola_chronology(html, 'fixture')
    assert len(rows) == 1 and rows[0]['value'] == 20
    assert len(skipped) == 1


def test_cholera_duplicate_conflict_is_not_summed():
    base = {'SpatialDimType': 'COUNTRY', 'SpatialDim': 'NGA', 'TimeDim': 2015, 'Id': 1, 'NumericValue': 10}
    rows = cholera_history([base, {**base, 'Id': 2, 'NumericValue': 20}], 'fixture', {'NGA': 'Nigeria'})
    assert rows[0]['points'][0]['value'] is None
