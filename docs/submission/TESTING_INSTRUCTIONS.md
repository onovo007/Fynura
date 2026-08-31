# Judge-facing testing instructions

1. Open https://fynura-g7sjcbc4ua-uc.a.run.app/welcome and select **Continue with Google**. Use your Google account, including Gmail; no new Fynura password is required.
2. Complete country/consent onboarding if shown, then enter Fynura. Existing sessions may go directly to the app. Organizational Google policies may restrict sign-in; contact the submitter if blocked.
3. In **Signals worth watching**, inspect the map legend and a country marker. Missing reports do not mean no cases.
4. Select Cholera and Africa. Try Reported cases. Other metrics can lack eligible data; an unavailable metric is not zero.
5. Review **Evidence at a glance**. Check the reporting cutoff, country/scope and source, not only the retrieval date.
6. Open **Threat trajectories** → Ebola. The title identifies Democratic Republic of the Congo. Inspect labels, metric selector and accessible data table.
7. In historical evidence, choose Measles and United States of America. Inspect a cell/point and the reported-period total. Partial coverage is labeled.
8. In **Ask Fynura**, ask: “What is herd immunity, and why does it matter for measles? Answer briefly with official sources.” Leave selected-visual context unchecked. Wait for research/source-checking progress.
9. Ask “Why does vaccination coverage matter?” as a follow-up. Inspect **Evidence support** and **Sources**, and follow an inline source link. Stored surveillance answers separately show numerical Evidence confidence; neither is a probability of correctness.
10. Optionally download the response or use dictation, reviewing the transcript before Send. Use Sign out when finished.

For a chart-specific query, use its Ask action or explicitly enable selected-visual context. The exact answer may vary as search results change. Research can take longer than a short definition; failures should be visible rather than replaced with unsupported claims.

## Developer verification

```sh
python -m pytest -q
node tests/frontend_heatmap.cjs
node tests/frontend_voice.cjs
```

Automated checks cover numerical safeguards, routing and frontend interactions. They do not establish clinical accuracy or complete browser coverage.

Live optional probe: `python tests/conversation_live_probe.py`, with ADC and Vertex permissions. It calls a paid external model.
