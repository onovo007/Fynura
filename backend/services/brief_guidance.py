"""Reviewed WHO background. Never treated as outbreak-specific demographic evidence."""

GUIDANCE = {
    'cholera': {
        'url': 'https://www.who.int/news-room/fact-sheets/detail/cholera',
        'published': '2024-12-05',
        'people': 'People without reliable safe water and sanitation are particularly exposed. Displacement, conflict and climate emergencies can disrupt these services.',
        'spread': 'Infection follows consumption of water or food contaminated with Vibrio cholerae. Infected people can shed bacteria even without symptoms.',
        'actions': [('Protect water', 'Improve safe water, sanitation and hygiene, including water-quality monitoring.'), ('Detect and respond', 'Strengthen surveillance and laboratory confirmation; engage communities in reporting and prevention.'), ('Prevent severe outcomes', 'Ensure rapid access to rehydration and clinical care; use oral cholera vaccination as part of an integrated response.')],
    },
    'measles': {
        'url': 'https://www.who.int/news-room/fact-sheets/detail/measles',
        'published': '2026-07-15',
        'people': 'Non-immune people can be infected. Unvaccinated young children and pregnant people face particularly serious complications; malnutrition and weakened immunity increase vulnerability.',
        'spread': 'Measles spreads through infectious air when an infected person breathes, coughs or sneezes. Transmission can precede the rash.',
        'actions': [('Close immunity gaps', 'WHO recommends two vaccine doses for children through national immunization programmes.'), ('Reach missed communities', 'Combine routine vaccination with campaigns where case rates are high and reach displaced populations.'), ('Support clinical care', 'Prompt assessment and supportive care address dehydration and complications. Treatment decisions belong to qualified clinicians.')],
    },
    'ebola': {
        'url': 'https://www.who.int/news-room/fact-sheets/detail/ebola-disease',
        'published': '2025-04-24',
        'people': 'Close contacts, caregivers and health workers can be exposed when infection-control precautions are inadequate. Contact with a deceased person during burial can transmit infection.',
        'spread': 'Transmission occurs through direct contact with infected blood or body fluids, or contaminated objects, through broken skin or mucous membranes. People do not transmit Ebola before symptoms.',
        'actions': [('Find and follow contacts', 'Combine surveillance, laboratory diagnosis and contact tracing.'), ('Prevent exposure', 'Use infection prevention and control, safe and dignified burials, and community engagement.'), ('Provide appropriate care', 'Early intensive supportive care improves survival. Vaccination and specific therapies depend on the virus; approved products are not available for every Ebola disease.')],
    },
}


def guidance_sections(threat):
    g = GUIDANCE.get(threat)
    if not g:
        return [], [], []
    citation = {'organization': 'World Health Organization', 'title': threat.title()+' fact sheet (general guidance)', 'url': g['url'], 'published': g['published'], 'reviewed_on': '2026-08-30'}
    sections = [
        {'title': 'Who is vulnerable', 'text': g['people'], 'kind': 'WHO general background', 'source_url': g['url']},
        {'title': 'How transmission occurs', 'text': g['spread'], 'kind': 'WHO general background, not a reconstructed outbreak transmission chain', 'source_url': g['url']},
        {'title': 'WHO control priorities', 'text': ' '.join(title+': '+text for title, text in g['actions']), 'kind': 'Official general guidance, reviewed 30 August 2026', 'source_url': g['url']},
    ]
    actions = [{'title': title, 'text': text, 'source_url': g['url']} for title, text in g['actions']]
    return sections, actions, [citation]
