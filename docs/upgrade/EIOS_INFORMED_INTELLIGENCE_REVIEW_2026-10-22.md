# EIOS-informed public-health intelligence review

## Scope

This review compares Fynura's public-health intelligence workflow with published WHO EIOS practices. It does not imply WHO affiliation, EIOS access or endorsement.

## Published EIOS operating model

WHO describes EIOS as an all-hazards, One Health initiative for detecting, contextualizing, assessing and sharing information about potential public-health threats from open sources. Its technology processes large volumes of public web content and applies language processing, entity recognition, categorization and analyst-configured rules. The community model combines technology with trained public-health practitioners.

EIOS complements rather than replaces formal International Health Regulations notification and verification. WHO also states that it cannot guarantee the completeness, accuracy or quality of third-party content surfaced through the initiative. These boundaries are directly relevant to any public-facing intelligence product.

Primary references:

- WHO, [Epidemic Intelligence from Open Sources](https://www.who.int/initiatives/eios)
- WHO, [EIOS technology](https://www.who.int/initiatives/eios/eios-technology)
- WHO, [EIOS community of practice](https://www.who.int/initiatives/eios/eios-community-of-practice)
- WHO, [EIOS training](https://www.who.int/initiatives/eios/eios-training)

## Practices adopted in Fynura

1. **Broad detection, explicit verification.** Research can search current open sources, but canonical surveillance cards and maps remain tied to traceable observations from configured authorities.
2. **Human-inspectable provenance.** Each public claim exposes its source, reporting cutoff, publication date, retrieval time, definition and evidence identifier.
3. **No automatic equivalence between mentions and events.** Preparedness advisories, confirmed cases, deaths and historical outbreak records retain separate indicators.
4. **Country and period consistency.** Monitor, Verify and Ask use the same canonical workspace contract. Detect uses a separate historical archive and labels it accordingly.
5. **Visible uncertainty.** Conflicts, gaps and reporting delays remain visible; absence of a report is not represented as zero activity.
6. **Operationally useful advisory format.** Country-programme questions are organized around priority geographies and populations, surveillance actions, control actions, and evidence gaps or escalation triggers.

## Movement and connectivity data

Fynura does not currently operate a production feed for mobility, passenger flights or migration. Public WHO EIOS materials reviewed here establish open-source event intelligence capabilities, but do not by themselves establish a reusable EIOS mobility, aviation or migration dataset for Fynura.

Potential sources require separate assessment because they answer different questions:

| Context | Candidate source type | Intended use | Main constraint |
|---|---|---|---|
| Passenger connectivity | Licensed itinerary or schedule data | Route-connected importation context | Licensing, coverage and passenger-versus-aircraft distinction |
| Aircraft movement | OpenSky-style aircraft telemetry | Aircraft traffic patterns | Does not measure passenger journeys |
| Displacement | IOM Displacement Tracking Matrix | Displacement in covered settings | Uneven geographic and temporal coverage |
| Migration structure | UN DESA migrant-stock data | Long-run population context | Not a near-real-time movement signal |
| Aggregated mobility | Privacy-preserving mobility programmes | Relative movement change | Access agreements, privacy and representativeness |

Before any feed becomes operational, Fynura should record licensing, refresh frequency, geographic completeness, privacy controls, denominators, validation results and failure behavior. Movement indicators must remain contextual covariates and must not be presented as proof of disease transmission.

## Next validated increment

Add a source registry for contextual datasets, implement one licensed or openly reusable pilot feed, retain it outside canonical case totals, and evaluate whether it improves predefined advisory decisions. The production interface should display the contextual source, date, geographic resolution and limitations beside any movement-informed statement.
