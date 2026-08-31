"""Opt-in paid Vertex availability check; emits metadata, never credentials."""
import json
import sys
from google import genai
from google.genai import types

with genai.Client(vertexai=True, project="fynura-public-health", location="global",
                  http_options=types.HttpOptions(timeout=90000)) as client:
    response = client.models.generate_content(
        model=sys.argv[1],
        contents="Search WHO and explain in two sentences what herd immunity means for measles. Cite the source.",
        config=types.GenerateContentConfig(
            max_output_tokens=2000,
            thinking_config=types.ThinkingConfig(thinking_level="LOW"),
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )
    metadata = response.candidates[0].grounding_metadata
    print(json.dumps({"requested_model": sys.argv[1], "model_version": response.model_version,
                      "answer": response.text,
                      "grounding_chunks": len(metadata.grounding_chunks or []) if metadata else 0,
                      "grounding_supports": len(metadata.grounding_supports or []) if metadata else 0}))
