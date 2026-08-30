"""Bounded educational answers; no operational harm instructions."""
import re


def science_answer(question):
    q = question.lower()
    if re.search(r'(deliberately|intentionally|weaponiz\w*|evade|conceal|falsify|fabricate).{0,65}(spread|disease|pathogen|surveillance|detection|data)', q):
        return "I can't help deliberately spread disease, conceal transmission, or falsify surveillance. I can explain responsible surveillance, prevention, and evidence interpretation."
    if re.search(r'\b(diagnose me|what medication should i take|what dose should i take)\b', q):
        return 'Fynura cannot diagnose you or prescribe individual treatment. Please consult a qualified clinician; I can explain population-level evidence and official public-health guidance.'
    if any(word in q for word in ('cusum', 'baseline', 'statistical signal', 'signal elevated', 'deviation begin')):
        return ('CUSUM accumulates departures from a defined historical surveillance baseline. It is not a forecast or an official outbreak declaration. '
                'The current Fynura snapshots lack an eligible historical baseline, so no live statistical alert or deviation start date is claimed. '
                'See Early Signal Detection in Fynura Docs for eligibility, thresholds, seasonality and missing-data limitations.')
    if 'infection fatality' in q or re.search(r'\bifr\b', q):
        return 'Infection fatality ratio requires all infections, including undiagnosed infections. It cannot be estimated by dividing deaths by reported cases. Current surveillance snapshots do not support an IFR estimate.'
    if 'attack rate' in q:
        return 'Attack rate is the proportion of a defined population at risk that becomes a case during a specified outbreak period. A compatible population denominator and time window are required; Fynura does not infer missing denominators.'
    return None
