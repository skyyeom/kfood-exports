# 05 — Roadmap & Release Plan

> Milestones are scope gates, not dates. Each milestone ends with a demoable increment and an exit check.

## 1. Prioritisation logic
We order work by **(a) what the challenge scores**, **(b) risk reduction** and **(c) dependency order**.

| Capability | Business impact | Agent completeness | AI capability | Risk if late | Order |
|---|---|---|---|---|---|
| Data foundation + corrections (volume, hubs, provenance) | ●●● (defensible TOP3) | ●● (accuracy) | ●● | High: everything depends on it | 1 |
| Scoring + P(TOP3) + reason packs | ●●● | ●● | ●● | High | 2 |
| Dashboard (API + UI) | ●● | ●●● (usable demo) | ● | Medium | 3 |
| Agent + verifier + RAG + report | ●●● | ●●● | ●●● | High: hardest to get right | 4 |
| Monitoring + email + simulation | ●● (continuous value) | ●● | ●● | Medium | 5 |
| Evaluation + proposal | ●● | ●●● (proves accuracy) | ●●● | High: unproven claims lose points | 6 (continuous) |

## 2. Milestones

| Milestone | Stories | Demo at exit | Exit criteria |
|---|---|---|---|
| **M0 — Discovery** ✅ | — | PM docs | Problem, market and data analysis, PRD, stories, roadmap, metrics, decision log done |
| **M1 — Data foundation** | US-31, US-32, US-33 (schema), Trends snapshot, Taiwan decision | Indicator tables + data dictionary | Pipeline reproduces the [03](03_data_analysis.md) numbers within ±1%; every row has provenance; coverage report generated |
| **M2 — Scoring MVP** | US-01…US-07, US-10, US-11 (engine side), forecast engine (US-09 backend) | Notebook/CLI TOP3 per category and preset | Unit tests for normalisation, weights, filters, P(TOP3); TOP3 matches the [03 §3](03_data_analysis.md) preliminary screen with the same settings |
| **M3 — Dashboard MVP** | US-01…US-08 UI, US-09 chart, US-30, KO/EN | Deployed preview: sliders → TOP3 cards → country drawer | p95 re-rank ≤ 500 ms; cold-start loader works; Lighthouse accessibility ≥ 90 |
| **M4 — Agent & report** | US-12…US-18 | Ask → grounded answer with citations → agent changes the UI → TOP3 report → PDF | Golden-set targets (PRD §5.2) met; fuzz tests pass |
| **M5 — Monitoring** | US-20…US-26 | Watchlist → simulated anomaly → re-rank + alert + email | Daily job green 7 runs in a row; simulation end-to-end Playwright test passes; isolation tests pass |
| **M6 — Submission** | US-19, evaluation reports, proposal, demo video | Final demo | All PRD §5 metrics reported; README baseline + measured time; demo video recorded |

**Critical path:** M1 → M2 → M3 → M4. M5 can start after M2 (anomaly engine) and M3 (alerts UI). Evaluation assets (golden set, backtests) are built alongside M2–M4, not at the end.

## 3. Scope-cut order (if we run short)
Cut from the bottom first:
1. Could-haves: US-27, US-28, US-29.
2. TOPSIS cross-check (US-10).
3. FX and regulation-hash signals. Keep the trade and TOP3-change signals.
4. LLM-written briefs. Template-only emails are acceptable.
5. Login + watchlists. The simulation then emails a fixed demo address.

**Never cut:** provenance, data corrections, P(TOP3), the verifier, the evaluation report and cold-start handling. These protect the accuracy and credibility scores.

## 4. Judge demo script (target ≤ 5 minutes)
1. Open the site → warm-up loader → dashboard (cached TOP3 visible immediately).
2. Show the default TOP3 with P(TOP3) and the reason chips; open one country's evidence.
3. Switch the preset "Scale" → "Growth/entry", then the category to **Ice cream**, and show how the TOP3 changes and why.
4. Toggle "include hubs" to show the Netherlands jump, explaining *why the tool corrects for hubs by default*.
5. Ask the agent: "필리핀이 말레이시아보다 높은 이유는?" and get a cited answer plus the tool trace.
6. Ask: "인도네시아에 ZERO 쿠키를 수출하려면 할랄 인증이 언제부터 필요해?" and get the PP 40/2026 answer (18 Oct 2028) with citation.
7. Tell the agent "관세 10% 넘는 국가 제외해줘": the UI updates, with undo.
8. Generate the TOP3 report → Export PDF.
9. Run the simulation (+45% Vietnam): show the re-rank, chart highlight, alert and the `[SIMULATION]` email in the inbox.
10. Close with the evaluation dashboard: faithfulness, citation precision, backtest and time-savings numbers.

## 5. 본선 extension plan
- Load Lotte field data (sales, distributor, pricing) via the common schema (`source=lotte_field`).
- Add an internal-performance pillar (e.g. sell-through, margin by market).
- Add HS 6-digit or 관세청 10-digit product mapping (Pepero, ZERO, World Cone).
- Optional paid data adapters (Euromonitor/Nielsen) if provided.
- Run user validation with Lotte staff: confirm the personas, the baseline (Q4) and the presets.
