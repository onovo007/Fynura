"""Exploratory seasonal CUSUM of one compatible monthly historical series."""
from math import sqrt, isfinite
from statistics import mean
from backend.services.history import catalog


def seasonal_review(points):
    result = {'ready':False, 'status':'Insufficient longitudinal evidence', 'points':[],
              'model':'fynura-seasonal-cusum-v1',
              'note':'The available months do not form a continuous six-year comparison period. Explore individual reports in Historical evidence.'}
    if len({p['period'] for p in points}) != len(points):
        return {**result, 'note':'Repeated reporting periods need review before comparison.'}
    ordered = sorted(points, key=lambda p:p['period'])
    while ordered and ordered[-1]['value'] is None:
        ordered.pop()
    suffix=[]; previous=None
    for point in reversed(ordered):
        value=point['value']
        if value is None or not isfinite(value) or value < 0 or not point.get('evidence_id'):
            break
        year, month = map(int, point['period'].split('-'))
        index=year*12+month
        if previous is not None and previous-index != 1:
            break
        suffix.append(point);previous=index
    if len(suffix)<72:
        return {**result,'available_months':len(suffix)}
    rows=list(reversed(suffix[:72]));baseline=rows[:60];monitor=rows[60:]
    expected={month:mean(p['value'] for p in baseline if int(p['period'][5:7])==month) for month in range(1,13)}
    scale=sqrt(sum((p['value']-expected[int(p['period'][5:7])])**2 for p in baseline)/(60-12))
    if scale==0:
        return {**result,'status':'Explore reported counts','note':'The historical pattern has too little variation for this comparison.'}
    statistic=0;review=[]
    for p in monitor:
        exp=expected[int(p['period'][5:7])]
        statistic=max(0,statistic+(p['value']-exp)/scale-0.5)
        review.append({**p,'expected':round(exp,2),'cusum':round(statistic,3),'threshold':5})
    crossings = [p['period'] for p in review if p['cusum'] >= 5]
    return {'ready':True,'status':'Sustained increase in reports' if statistic>=5 else 'No sustained increase detected',
        'model':'fynura-seasonal-cusum-v1', 'baseline_count':60, 'monitoring_count':12,
        'first_threshold_crossing':crossings[0] if crossings else None,
        'points':review,'baseline_start':baseline[0]['period'],'baseline_end':baseline[-1]['period'],
        'baseline_evidence_ids':[p['evidence_id'] for p in baseline], 'baseline_sd':scale,
        'reporting_cutoff':monitor[-1]['period'],'threshold':5,'k':0.5,
        'note':'Historical screening only. Reporting changes can affect the pattern; this is not an outbreak declaration.',
        'method':'Each month is compared with the same month in the preceding five-year baseline. The last 12 months are monitored separately. Thresholds have not been validated for operational alerts.'}


def early_history(country='USA'):
    data=catalog()['datasets']['measles']
    chosen=next((c for c in data['countries'] if c['code']==country),None)
    if chosen is None:
        raise ValueError('Country unavailable')
    return {**seasonal_review(chosen['points']), 'country':country, 'geography':chosen['name'],
        'countries':[{'code':c['code'],'name':c['name']} for c in sorted(data['countries'], key=lambda c:c['name'])],
        'source_url':data['source_url'],'source':data['source'],'retrieved_at':data['retrieved_at'],
        'coverage':[{'threat':'Cholera','status':'Annual history available','description':'Explore annual country totals in Historical evidence. Monthly reports are needed for this signal comparison.'},
                    {'threat':'Ebola','status':'Outbreak history available','description':'Compare separate outbreaks in Historical evidence. Outbreak totals cannot be combined into a monthly monitoring series.'}]}
