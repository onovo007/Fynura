# Upgrade handover

## Current release boundary

This repository now contains a tested Phase 1 NCDC parsing foundation and truthful Nigeria availability status. It does not yet schedule NCDC retrieval or display NCDC epidemiological values in production.

## Next engineering increment

1. Add an allowlisted NCDC report index retriever with rate limits and checksum deduplication.
2. Store `raw_documents` and `extracted_observations` in additive, versioned repositories.
3. Build human review for table/page extraction exceptions and geographic ambiguities.
4. Complete the official NBS LGA crosswalk and regression coverage.
5. Add the Nigeria country → state → LGA interface only for validated published rows.
6. Run the full legacy suite with provider calls stubbed; investigate the local Ask Fynura integration wait before deployment.
7. Deploy to a non-production revision, verify source status and rollback, then request explicit authorization for production changes.

Deployment and repository publication are separate release operations. This handover does not treat local implementation as proof of production activation; verify the deployed revision and public endpoints before changing source status.
