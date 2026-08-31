# Fynura research chat

Updated 31 August 2026.

## Two evidence paths

The interactive chat calls `/api/chat/stream`: a request-scoped Google ADK
`LlmAgent` and `Runner` execute Gemini 3.7 Flash on Vertex AI's global
endpoint with Google Search grounding. This is a real model invocation, not the
shared `/api/ask` and `/api/chat/stream` intelligence dispatcher. A second ADK source-review pass
searches original reports to check key claims and improve the draft before display.
Scientific questions use a single research pass. If source support is unavailable,
a separate bounded model call can explain established methods, clearly labeled
GENERAL SCIENTIFIC EXPLANATION with LIVE VERIFICATION UNAVAILABLE. It does not
invent citations or substitute for current surveillance. Default model answers
target 80–180 words, with longer reports on explicit request. High-confidence
intent rules plus a schema-constrained semantic classifier cover methods beyond
the three diseases. Both endpoints execute the same dispatcher and guardrails.
Structured evidence and infographic workflows remain available.

Dashboard surveillance still uses deterministic source adapters and verification.
Chat research does not update or certify those canonical observations. Search is
on demand, not continuous monitoring of every news source. Publication/reporting
delays still apply. Search may omit relevant sources or return outdated results.

The model prioritizes official authorities, uses news as context, distinguishes
republication from independent confirmation, and is instructed to describe
conflicts and missing age/sex data. These are behavioral safeguards, not a claim
that every response has undergone independent expert verification. The UI exposes
Google grounding links inline and collectively, plus an evidence-coverage panel.
No model-generated percentage is presented as a probability of factual correctness.
Missing grounding for live research fails closed rather than returning an
apparently verified answer. Scientific fallback is educational, not live-verified.

## Context and privacy

General questions do not automatically use the selected chart. Users can opt in
with “Include the selected visual in my question”; chart-specific question buttons
provide explicit context. Up to eight prior question/answer pairs remain in page
memory and are sent to the model for follow-ups. They disappear on reload and are
cleared by the New conversation button. Prior messages are
not trusted as evidence. ADK sessions are ephemeral per request. Provider-side
processing is still subject to Google Cloud terms; do not enter patient identifiers.

## Progress and capacity

The stream shows real request stages: loading stored evidence, waiting for Gemini
research, and formatting evidence links. It does not expose private chain of
thought or claim to stream tokens. There is a 240-second combined research/review timeout and four
concurrent streaming requests per application process. Extra streams wait up to
five seconds before receiving a busy message. Preview model availability, cost,
latency, project quota and Cloud Run scaling remain operational considerations.

Configuration: `FYNURA_CHAT_MODEL` and `FYNURA_CHAT_LOCATION`. No API key is sent
to the browser. The Cloud Run runtime service account needs Vertex AI access.

## Guardrails and evidence support

Biological-harm and surveillance-fraud intent rules execute before retrieval,
including on `/api/ask`. Provider instructions cover every research and classifier
call. These controls are tested defenses, not a guarantee against every adversarial
paraphrase. Legitimate HIV/sexual-health questions remain supported. Refusals do
not enter client conversation memory. Explicit new topics override stale charts.
Scientific answers have qualitative evidence support; canonical surveillance
answers keep deterministic confidence, metrics, cutoff and original-source links.
WHO-derived OWID observations share WHO origin for independence scoring.

## Dictation

The microphone is a labeled SVG button, not an ambiguous emoji. Clicking Dictate
requests browser speech-recognition permission. Listening, permission denial,
missing microphone, no speech, network errors and start failures are visible.
Dictation never automatically sends a question. Review the transcript and Send.
Raw audio is not recorded by Fynura; the browser speech service may process audio.
Chrome microphone permission and Windows microphone privacy settings must allow
access. Actual audio capture requires a user microphone test.

## Acceptance checks

Provider recovery: both chat endpoints automatically retry Gemini HTTP 429,
500, 502, 503 and 504 failures before an answer is delivered. There are at most
three orchestration attempts, separated by 2–3 and 4–5 seconds of jittered
backoff. Streamed chat displays retry progress. One 250-second deadline covers
classification, research and backoff; SDK retries are disabled to avoid nested
retry multiplication. Authentication, validation and other non-transient errors
are not retried. Cancellation stops work and an already delivered answer is never
replayed. Persistent failure remains visible without substituting cached research.
Retries improve recovery but cannot remove provider quota or capacity limits;
they may repeat model/search work and incur additional usage. Sanitized retry and
recovery log events contain status codes and attempt counts, not user prompts.

1. Ask a broad current-threat question while a disease chart is selected; check the
   response covers the question rather than only that chart.
2. Ask a specific country/disease question and inspect source links and dates.
3. Ask for demographics; distinguish measured data from general risk groups.
4. Ask a follow-up, then a new topic, checking conversation context is appropriate.
5. Select explicit chart context and ask why the plotted counts changed.
6. Check Dictate, permission denial, successful transcript review and Send.
7. Check research errors/busy states are visible and no stale template substitutes
   for live research. Review numerical claims against the linked primary source
   before publishing or using a response for public-health decisions.
