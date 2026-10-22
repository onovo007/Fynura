# Phase 1 security and privacy review

- The adapter accepts aggregate public-health report tables only. It has no patient, contact or fine-grained movement fields.
- Live retrieval is disabled; no credentials, paid services or production writes were introduced.
- Source documents are identified by SHA-256 checksums. Normalized observations retain page/table provenance and parser version.
- Empty cells are skipped as missing; explicit published zeros remain zero.
- Duplicate disease/indicator/period/interval keys fail closed.
- LGA data cannot be published until a report-specific code match passes ambiguity review.
- Future PDF text is untrusted input. It must never be passed as instructions to an LLM or used to alter system behavior.
- Public and restricted datasets require separate collections and role-based access before institutional data are introduced.
