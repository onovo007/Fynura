"""Resolve explicit disease names before any stale presentation context."""
import re

from backend.models.domain import ContextEnvelope


def resolve_context(request):
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
