"""Bounded educational answers; no operational harm instructions."""
import re


def is_immunity_definition(question):
    return bool(re.fullmatch(r"(?:what is|what's|what does|define|meaning of)\s+(?:herd|heard)\s+immunity(?:\s+mean)?[?.!]*", question.lower().strip()))


def science_answer(question):
    q = question.lower()
    if is_immunity_definition(question):
        return ('Herd immunity is indirect protection from an infectious disease when enough people in a community are immune, making it harder for the infection to spread. '
                'It helps protect people who cannot be vaccinated or may not develop strong immunity. Vaccination is the safest way to build this community protection. '
                'The level of immunity needed varies by disease, and protection is not absolute.')
    if re.search(r'(deliberately|intentionally|weaponiz\w*|evade|conceal|falsify|fabricate).{0,65}(spread|disease|pathogen|surveillance|detection|data)', q):
        return "I can't help deliberately spread disease, conceal transmission, or falsify surveillance. I can explain responsible surveillance, prevention, and evidence interpretation."
    if re.search(r'\b(diagnose me|what medication should i take|what dose should i take)\b', q):
        return 'Fynura cannot diagnose you or prescribe individual treatment. Please consult a qualified clinician; I can explain population-level evidence and official public-health guidance.'
    if any(word in q for word in ('cusum', 'baseline', 'statistical signal', 'signal elevated', 'deviation begin')):
        return ('CUSUM accumulates departures from a defined historical surveillance baseline. It is not a forecast or an official outbreak declaration. '
                'Fynura offers a historical monthly measles comparison for countries with a suitable reporting sequence. Annual totals and separate outbreaks are explored separately. '
                'See Early Signal Detection in Fynura Docs for eligibility, thresholds, seasonality and missing-data limitations.')
    if 'infection fatality' in q or re.search(r'\bifr\b', q):
        return 'Infection fatality ratio requires all infections, including undiagnosed infections. It cannot be estimated by dividing deaths by reported cases. Current surveillance snapshots do not support an IFR estimate.'
    if 'attack rate' in q:
        return 'Attack rate is the proportion of a defined population at risk that becomes a case during a specified outbreak period. A compatible population denominator and time window are required; Fynura does not infer missing denominators.'
    return None
