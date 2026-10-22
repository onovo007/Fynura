# Ebola regional coverage correction

## Verified map behavior

The Africa `Reported signal` view distinguishes two evidence classes:

- Confirmed outbreak activity: Democratic Republic of the Congo, Uganda and Kenya, based on WHO Disease Outbreak News.
- Preparedness monitoring: Nigeria, based on the NCDC national advisory. The Nigeria popup explicitly states that no confirmed Ebola case was reported.

The `Reported cases`, `Deaths` and `Crude CFR` metrics exclude preparedness advisories. This prevents a national readiness notice from being displayed as a case count.

## Current source cutoffs

- DRC: WHO DON619, reporting through 6 October 2026.
- Kenya: WHO DON619, imported case reported through 6 October 2026.
- Uganda: WHO DON617, cumulative country totals reported through 7 September 2026.
- Nigeria: NCDC preparedness statement, status through 6 October 2026.

Individual WHO report failures are isolated. A refresh still requires at least two compatible DRC reports so that an inaccessible page cannot silently produce an unsupported trajectory.
