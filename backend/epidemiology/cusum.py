"""Conservative one-sided standardized CUSUM; not an outbreak forecast."""
from datetime import date
from itertools import pairwise
from math import isfinite
from statistics import mean, stdev

MODEL = 'fynura-cusum-1.0'


def detect(rows, frequency='weekly', minimum_history=None, k=0.5, h=5.0,
           seasonal=False, revised=False, structural_break=False):
    minimum = minimum_history if minimum_history is not None else (26 if frequency == 'weekly' else 24)
    result = {'model_version': MODEL, 'eligibility': 'NOT ELIGIBLE',
              'signal': 'INSUFFICIENT HISTORY', 'reasons': [], 'points': [],
              'baseline_method': 'fixed historical mean and sample standard deviation',
              'minimum_history': minimum, 'k': k, 'threshold': h,
              'limitations': ['Engineering defaults, not validated disease-specific thresholds.',
                              'A statistical alert is not an official outbreak declaration or a forecast.']}
    if frequency not in {'weekly', 'monthly'} or minimum < 2 or k < 0 or h <= 0:
        raise ValueError('Invalid CUSUM configuration')
    if len(rows) < minimum + 1:
        result['reasons'].append(f'Requires {minimum} baseline observations plus at least one monitoring observation.')
    if not rows:
        return result
    keys = {(r.get('threat'), r.get('geography'), r.get('indicator'), r.get('case_definition'), r.get('unit')) for r in rows}
    if len(keys) != 1 or any(any(v is None for v in key) for key in keys):
        result['reasons'].append('Inconsistent or missing series definitions.')
    if any(r.get('value') is None or not isfinite(r['value']) or r['value'] < 0 or not r.get('evidence_ids') for r in rows):
        result['reasons'].append('Missing values or provenance; missing observations are not zero-filled.')
    try:
        rows = sorted(rows, key=lambda r: r['date'])
        dates = [date.fromisoformat(r['date']) for r in rows]
        regular = all((b-a).days == 7 if frequency == 'weekly' else
                      (b.year-a.year)*12+b.month-a.month == 1 for a,b in pairwise(dates))
        if not regular:
            result['reasons'].append('Missing, duplicate, or irregular reporting periods.')
    except (KeyError, ValueError):
        result['reasons'].append('Reporting dates are invalid.')
    if revised or structural_break:
        result['reasons'].append('Reporting revision or structural break requires baseline review.')
    if result['reasons']:
        return result
    if seasonal:
        result.update(eligibility='LIMITED', signal='METHOD REVIEW REQUIRED')
        result['reasons'].append('Seasonality is not modeled by this baseline; statistical signals are withheld.')
        return result
    baseline = [r['value'] for r in rows[:minimum]]
    expected, scale = mean(baseline), stdev(baseline)
    if scale == 0:
        result['reasons'].append('Baseline has zero variance; standardized CUSUM is undefined.')
        return result
    result.update(eligibility='ELIGIBLE', expected=expected, baseline_sd=scale,
                  baseline_start=rows[0]['date'], baseline_end=rows[minimum-1]['date'],
                  baseline_evidence_ids=sorted({e for r in rows[:minimum] for e in r['evidence_ids']}))
    statistic = 0.0
    for row in rows[minimum:]:
        deviation = (row['value']-expected)/scale
        statistic = max(0, statistic+deviation-k)
        signal = 'STRONG SIGNAL' if statistic >= 2*h else 'ELEVATED SIGNAL' if statistic >= h else 'WATCH' if statistic >= h/2 else 'NO STATISTICAL SIGNAL'
        result['points'].append({**row, 'observed': row['value'], 'expected': expected,
                                 'standardized_deviation': deviation, 'cusum': statistic,
                                 'threshold': h, 'signal': signal, 'model_version': MODEL})
    result['signal'] = result['points'][-1]['signal']
    return result
