from backend.services.early_history import seasonal_review, early_history

def points():
    return [{'period':f'{2019+i//12}-{i%12+1:02d}', 'value':10+(i%12)*2+(i//12)%3,
             'evidence_id':str(i)} for i in range(72)]

def test_seasonal_baseline_excludes_monitoring_and_retains_provenance():
    rows=points();result=seasonal_review(rows)
    assert result['ready']
    assert len(result['points'])==12
    assert len(result['baseline_evidence_ids'])==60
    rows[-1]['value']=1000
    changed=seasonal_review(rows)
    assert changed['baseline_sd']==result['baseline_sd']
    assert changed['status']=='Sustained increase in reports'

def test_missing_duplicate_and_short_history_are_not_filled():
    rows=points();rows[50]['value']=None
    assert not seasonal_review(rows)['ready']
    assert not seasonal_review(points()[:60])['ready']
    assert not seasonal_review(points()+[points()[-1]])['ready']

def test_real_monthly_history_and_other_disease_coverage():
    result=early_history('USA')
    assert result['ready'] and result['geography']=='United States of America'
    assert result['source']=='WHO'
    assert len(result['coverage'])==2
