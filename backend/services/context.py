"""Resolve explicit disease names before any stale presentation context."""
import re

from backend.models.domain import ContextEnvelope


def is_threat_overview(question):
    """Broad surveillance intent outranks ambient chart context, not explicit disease follow-ups."""
    q = re.sub(r'[^a-z0-9\s]', ' ', question.lower())
    q = re.sub(r'\s+', ' ', q).strip()
    if re.search(r'\b(measles|ebola|cholera)\b', q):
        return False
    if re.search(r'\b(this|these|selected|here|that)\b', q):
        return False
    return bool(re.search(r'\b(health threats?|public health situation|outbreaks|disease threats?|threats)\b', q)
                and re.search(r'\b(current|latest|now|today|monitoring|monitored|active|emerging|overview|what|whats|which)\b', q))


def resolve_context(request):
    if is_threat_overview(request.question):
        return None, None
    names = re.findall(r'\b(measles|ebola|cholera)\b', request.question.lower())
    explicit = list(dict.fromkeys(names))
    context = request.context
    selected = (context.threat_id or context.disease) if context else request.threat_id
    if len(explicit) == 1:
        threat = explicit[0]
        if selected != threat:
            context = context.model_copy(update={"threat_id": threat, "disease": threat}) if context and context.visual == "shared_workspace" else ContextEnvelope(threat_id=threat, disease=threat)
        return threat, context
    if len(explicit) > 1:
        return None, None  # Cross-threat overview; never silently choose one disease.
    return selected, context
