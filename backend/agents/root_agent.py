"""Google ADK agent graph. Deterministic tools own retrieval, arithmetic, and fusion."""
from backend.config import get_settings

try:
    from google.adk.agents import LlmAgent, SequentialAgent
    _model = get_settings().fynura_model
    discovery_agent = LlmAgent(name="discovery_agent", model=_model, instruction="Select only approved authoritative source candidates supplied by Fynura tools. Never use search snippets as epidemiological evidence.", output_key="discovery")
    extraction_agent = LlmAgent(name="extraction_agent", model=_model, instruction="Extract schema-valid observations from supplied authoritative content. Preserve dates, case definitions, and provenance. Never invent a value.", output_key="extraction")
    verification_agent = LlmAgent(name="verification_agent", model=_model, instruction="Explain deterministic evidence-fusion results, including unresolved conflicts. Do not change numeric values.", output_key="verification")
    briefing_agent = LlmAgent(name="briefing_agent", model=_model, instruction="Brief only from verified structured evidence. Cite observation IDs and communicate uncertainty.", output_key="briefing")
    root_agent = SequentialAgent(name="fynura_orchestrator", sub_agents=[discovery_agent, extraction_agent, verification_agent, briefing_agent])
except ImportError:
    root_agent = None

