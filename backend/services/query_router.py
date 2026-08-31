"""Shared request routing. Classifications are not scientific answers or evidence."""
from dataclasses import dataclass
import re

VERSION = "fynura-query-router-v1"
THREATS = ("measles", "ebola", "cholera")
REFUSAL = "I can't help deliberately spread disease, conceal transmission, target people for biological harm, or falsify surveillance. I can explain prevention, responsible surveillance or safe outbreak investigation."
SCOPE = "Fynura specializes in public health, epidemiology, health data, statistical science and related disciplines. I can help connect your question to those areas if useful."
MEDICAL = "Fynura cannot diagnose you or prescribe individual treatment. Please consult a qualified clinician. I can explain population-level evidence and official public-health guidance."

@dataclass
class Route:
    intent: str
    mode: str
    domain: str = "Public health"
    threat: str | None = None
    context: object | None = None
    reason: str | None = None

def safety_response(question):
    q = re.sub(r"[^a-z0-9 ]", " ", question.lower())
    # Harm intent is distinct from a legitimate discussion of a pathogen or sex.
    harmful = re.search(r"\b(weaponiz\w*|deliberately|intentionally|secretly|evad\w*|conceal\w*|falsif\w*|fabricat\w*|undetect\w*|malicious\w*)\b", q)
    target = re.search(r"\b(disease|pathogen\w*|virus|bacteri\w*|infect\w*|transmission|surveillance|detection|outbreak|health data|case counts)\b", q)
    optimization = re.search(r"\b(increase|enhance|optimi[sz]e|make|engineer)\b.{0,70}\b(virulence|transmissibility|more contagious|more lethal)\b", q)
    protective = re.search(r"\b(prevent|detect|stop|protect against|recognize|identify signs of)\b.{0,45}\b(deliberate|intentional|malicious|weaponiz)", q)
    if (harmful and target and not protective) or optimization:
        return REFUSAL
    if re.search(r"\b(diagnose me|what (?:medication|dose) should i take|prescribe (?:me|for me))\b", q):
        return MEDICAL
    return None

DOMAINS = {
    "Implementation science": r"implementation|re.?aim|fidelity|adoption|sustainability|feasibility",
    "Biostatistics / research methods": r"a\s*/?\s*b (?:test|testing)|randomi[sz]|regression|confidence interval|credible interval|bayesian|posterior|prior distribution|statistical|p[ -]?value|power|odds ratio|risk ratio|attributable|cohort|case.control|cross.sectional|quasi.experimental|interrupted time|difference.in.differences|sample size|meta.analysis|systematic review|survival analysis|study design|experimental design",
    "Health data science": r"cross.validation|overfitting|regularization|training|validation data|imputation|machine learning|data science|artificial intelligence|missing.data|data governance",
    "Spatial epidemiology": r"spatial|geospatial|geograph\w* weighted|geostatistic|getis|hotspot|\bgis\b",
    "Epidemiology / public health": r"incidence|prevalence|confound|selection bias|attack rate|epidemic curve|ecological study|syndromic|sentinel|event.based|active.{0,15}passive|reporting (?:delay|lag)|missing surveillance|reproductive number|reproduction number|\bcusum\b|\bifr\b|\bcfr\b|fatality|pathogen|herd immunity|heard immunity|transmission|vaccin|immun|hiv|sexual|reproductive health|contracept|maternal|nutrition|tuberculosis|malaria|one health|health system|health polic|health econom|environmental health|occupational|chronic.disease|public.health|epidemiolog|demograph|screening|risk communicat|journalist|policymaker|research ethic|evidence synth|forecast",
}

def route_question(request):
    q = request.question.lower().strip()
    refused = safety_response(q)
    if refused:
        return Route("UNSAFE" if refused == REFUSAL else "MEDICAL_LIMITATION", "safety", reason=refused)
    explicit = list(dict.fromkeys(re.findall(r"\b(measles|ebola|cholera)\b", q)))
    context = request.context
    selected = (context.threat_id or context.disease) if context else request.threat_id
    threat = explicit[0] if len(explicit) == 1 else selected
    if explicit and selected and selected != threat:
        from backend.models.domain import ContextEnvelope
        context = ContextEnvelope(threat_id=threat, disease=threat)
    elif explicit and context and not selected:
        context = context.model_copy(update={'threat_id':threat, 'disease':threat})
    registry = (re.search(r"\b(sources?|candidate|verified snapshots?|access limited|configured|operational)\b", q)
                and not re.search(r"\b(this|figure|observation|cite|supports? (?:this|the)|last answer)\b", q))
    if registry and ("fynura" in q or re.search(r"candidate|snapshot|access limited|operational|currently verified", q)):
        return Route("SOURCE_REGISTRY", "registry")
    if re.search(r"(?:what|which).*(?:diseases|threats).*fynura.*monitor|what.*fynura.*monitor", q):
        return Route("PRODUCT_SCOPE", "registry")
    definition = bool(re.match(r"(?:what (?:is|are|does)|define|explain|how (?:does|is|do)|why)\b", q))
    contextual = bool(re.search(r"\b(this|these|here|shown|selected|flagged)\b", q))
    if context and context.visual == "early_signal" and contextual:
        return Route("SIGNAL_INTERPRETATION", "signal", threat="measles", context=context)
    if context and context.visual == "historical" and not (definition and not contextual):
        return Route("HISTORICAL_SURVEILLANCE", "surveillance", threat=threat, context=context)
    if threat and re.search(r"\b(create|write|generate|prepare)\b.*\b(brief|briefing|report|infographic)\b", q) and not re.search(r"\b(?:19|20)\d{2}\b", q):
        return Route("OUTBREAK_BRIEF", "hybrid", "Outbreak interpretation", threat, context)
    knowledge_domain = next((domain for domain, pattern in DOMAINS.items() if re.search(pattern, q)), None)
    current = bool(re.search(r"\b(latest|current|happening|changed|how many|reported|situation|cite|which sources support)\b", q))
    hybrid = context and (contextual or re.search(r"what factors could|interpret (?:the|my)|explain (?:the|a) (?:rise|decline|pattern)", q)) and (knowledge_domain or re.search(r"could|interpret|explain|factors|limitations", q))
    if hybrid:
        return Route("VISUAL_INTERPRETATION", "hybrid", knowledge_domain or "Epidemiology", threat, context)
    if explicit and re.search(r"\bcfr\b", q) and not re.search(r"meaning|define|difference|calculated", q):
        return Route("CURRENT_SURVEILLANCE", "surveillance", threat=threat, context=context)
    if knowledge_domain and (not current or (definition and re.search(r"what (?:is|are)|define|how.*measured|why.*missing", q))):
        return Route("SCIENTIFIC_KNOWLEDGE", "knowledge", knowledge_domain)
    if threat and (current or contextual or re.search(r"cases|deaths|cfr|brief|infographic", q)):
        return Route("CURRENT_SURVEILLANCE", "surveillance", threat=threat, context=context)
    if len(explicit) > 1 or re.fullmatch(r"what['’]?s happening[?.!]*|what is happening[?.!]*", q):
        return Route("THREAT_OVERVIEW", "surveillance")
    if explicit and re.search(r"\b(?:19|20)\d{2}\b", q):
        return Route("HISTORICAL_SURVEILLANCE", "surveillance", threat=threat, context=context)
    if "threat" in q and "fynura" in q:
        return Route("PRODUCT_SCOPE", "registry")
    if re.search(r"current|latest|today|outbreak|health threat", q):
        return Route("LIVE_RESEARCH", "research", threat=threat, context=context)
    if knowledge_domain:
        return Route("SCIENTIFIC_KNOWLEDGE", "knowledge", knowledge_domain)
    return Route("CLASSIFY", "classify")
