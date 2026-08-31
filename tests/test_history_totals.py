import pytest

from backend.models.domain import AskRequest
from backend.services.history import historical_answer, historical_series, series_summary
from scripts.backfill_owid import parse_csv


def test_complete_monthly_sum_and_provenance():
    data = historical_series('measles', 'USA', 2019, 2019)
    summary = data['summary']
    assert summary['complete'] and summary['count'] == 12
    assert summary['total'] == sum(p['value'] for p in data['points'])
    answer = historical_answer(AskRequest(question='Total measles cases in the United States in 2019?'))
    assert f"{summary['total']:,}" in answer.answer
    assert len(answer.evidence_ids) == 12
    assert 'not a single outbreak total' in answer.answer


def test_gaps_never_claim_complete_total():
    data = historical_series('measles', 'USA', 2010, 2026)
    assert not data['summary']['complete']
    assert data['summary']['missing'] > 0
    assert 'partial' in data['summary']['label']


def test_separate_outbreaks_are_not_summed():
    assert series_summary([{'value': 30}], 'outbreak', 2010, 2026)['total'] is None


def test_owid_real_archive_and_yearly_answer():
    data = historical_series('cholera_annual', 'NGA', 2017, 2024)
    assert data['points'] and data['source'] == 'WHO via Our World in Data'
    assert data['points'][-1]['period'] == '2024'
    answer = historical_answer(AskRequest(question='Annual cholera totals in Nigeria from 2017 to 2024 via OWID'))
    assert answer.sources[0]['url'].startswith('https://ourworldindata.org/')
    assert 'WHO via Our World in Data' == answer.sources[0]['organization']


def test_owid_parser_excludes_regions_and_rejects_duplicates():
    data = 'Entity,Code,Year,Cases\nNigeria,NGA,2024,10\nWorld,OWID_WRL,2024,100\n'
    assert len(parse_csv(data, 'hash')) == 1
    with pytest.raises(ValueError):
        parse_csv(data + 'Nigeria,NGA,2024,12\n', 'hash')
