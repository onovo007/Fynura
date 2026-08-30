# Early signal detection

Fynura's CUSUM module identifies sustained departures from an expected surveillance baseline. A statistical alert is not equivalent to an official outbreak declaration and should be interpreted alongside epidemiological and public-health evidence.

The deterministic upper one-sided standardized statistic is `S[t] = max(0, S[t-1] + (observed[t] - mean)/sd - k)`. A fixed baseline uses the first 26 compatible weekly or 24 monthly observations, excluding the monitoring period. These configurable history lengths are initial engineering rules, not validated epidemiological thresholds. Zero baseline variance prevents calculation. No missing periods are imputed.

Defaults: k=0.5, h=5. No statistical signal: S<h/2; watch: h/2<=S<h; elevated: h<=S<2h; strong: S>=2h. These are transparent display rules, not calibrated sensitivity, specificity or outbreak probabilities. See the [NIST CUSUM reference](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc3131.htm).

Eligibility requires regular dates, consistent disease, geography, unit, indicator and case definition, complete values and evidence IDs. Flagged reporting revisions and structural breaks require baseline review. Seasonality is not modeled in version 1: seasonal series are LIMITED and signals are withheld. Structural-break and revision flags need source-specific review; the engine does not automatically infer all changes in reporting practice.

Current canonical snapshots do not provide a qualified longitudinal surveillance baseline. Ebola's short cumulative report sequence supports descriptive trajectory/change only. The public interface therefore shows insufficient history, not a fabricated statistical signal. Synthetic fixtures test computation only and are not live data or retrospective epidemiological validation. No predictive or lead-time performance is claimed.

IFR requires total infections including unreported infections; deaths divided by reported cases is not IFR. Fynura calculates crude CFR only for compatible observations with matching reporting periods, geography, definitions and units.
