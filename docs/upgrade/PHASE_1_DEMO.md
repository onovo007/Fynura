# Phase 1 review script

1. Open the source explorer and locate **Nigeria NCDC**. Confirm its status reads **monitored** rather than operational.
2. Open the Nigeria surveillance availability section. Confirm it displays **Validation in progress**, no live reporting cutoff and no unvalidated epidemiological count.
3. Call `GET /api/countries/nigeria/availability` and inspect the state-crosswalk count and LGA validation status.
4. Run the focused Phase 1 tests and show that incident and cumulative values remain separate, explicit zero is retained, missing values are skipped and duplicates fail closed.
5. Inspect one normalized fixture row and trace it to the official NCDC report URL, page and table.
6. Return to an existing WHO view to confirm that legacy evidence and functionality remain unchanged.
