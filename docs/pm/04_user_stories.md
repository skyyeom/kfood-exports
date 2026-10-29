# 04 — User Stories & Backlog

> Format: **As a** persona, **I want** capability, **so that** outcome. Acceptance criteria use Given/When/Then.
> Priority = MoSCoW (from the [PRD §7](../PRD.md#7-scope-moscow)). Size = relative story points (1, 2, 3, 5, 8, 13); no time estimates.
> Personas: P1 Strategy Manager · P2 Export Sales · P3 Executive · P4 Regulatory/QA · P5 Brand · J Judge.

---

## Story map (backbone → walking skeleton)

| Activity → | Set up screening | Rank & compare | Understand a country | Ask & verify | Share | Monitor |
|---|---|---|---|---|---|---|
| **Must** | US-01 category, US-02 presets | US-03 weights, US-04 P(TOP3), US-05 TOP3 cards | US-08 profile | US-12 chat, US-13 grounding, US-14 regulation Q&A | US-17 report, US-18 PDF | US-30 warm-up |
| **Should** | US-06 corrections toggle, US-07 entry mode | US-09 forecast, US-10 TOPSIS | US-11 strategic fit | US-15 agent drives UI, US-16 tool trace | — | US-20…US-26 alerts, simulation |
| **Could** | — | US-27 concentration view | US-28 competition context | — | — | US-29 tariff impact (monthly) |

---

## Epic 1 — Market Screening & Ranking

### US-01 · Choose category · Must · 3 pts · FR-1.4
**As** P1, **I want** to choose a category (sugar confectionery, chocolate, bakery & biscuits, ice cream, or all), **so that** the ranking reflects the product I'm planning to push.
- **Given** the dashboard is loaded, **when** I select "Ice cream (HS 2105)", **then** all scores, the TOP3 and the charts recompute using only HS 2105 data, and the selected category is shown in the header.
- **Given** a country has no data for the selected category, **then** it is shown at the bottom with a "no data" badge, not dropped silently.

### US-02 · Start from a preset · Must · 2 pts · FR-1.2
**As** P1, **I want** presets ("Scale markets", "Growth/entry markets", "Balanced"), **so that** I can start from a sensible strategy instead of an empty form.
- **Given** I pick a preset, **then** the weight sliders move to the preset values and the ranking updates.
- **Given** I change a slider after picking a preset, **then** the preset label changes to "Custom".
- Each preset shows a one-line description of its intent.

### US-03 · Adjust weights · Must · 5 pts · FR-1.1
**As** P1, **I want** to adjust pillar weights (market growth, size, trends, K-momentum, entry ease), **so that** I can see how priorities change the ranking.
- **Given** I move a slider, **when** I release it, **then** the leaderboard re-renders within **500 ms (p95)** with no layout shift.
- Weights always sum to 100% (auto-normalised) and the normalised values are displayed.
- Rank changes vs the previous state show as ▲/▼ indicators.

### US-04 · See how robust the TOP3 is · Must · 5 pts · FR-1.3
**As** P1, **I want** each country's probability of being in the TOP3 under weight uncertainty, **so that** I can tell leadership how robust the recommendation is.
- **Given** any weight setting, **then** each country shows P(TOP3) from ≥ 1,000 perturbation draws (±20%), and a tooltip explains the method.
- **Given** a TOP3 country has P(TOP3) < 50%, **then** its card shows a "fragile" badge.

### US-05 · TOP3 cards with reasons · Must · 5 pts · FR-1.9
**As** P3, **I want** each TOP3 card to show the top drivers, the weakest factor and sources, **so that** I understand *why* in seconds.
- Each card shows: rank, score, P(TOP3), 3 driver chips (e.g. "Volume growth +10.3%/yr"), 1 weakest-factor chip, and a "sources" link.
- Every number on the card links to its source, year and retrieval date.

### US-06 · Apply data corrections · Should · 3 pts · FR-1.5, FR-1.6
**As** P1, **I want** volume-based growth and hub exclusion on by default, with toggles, **so that** I'm not misled by price inflation or re-export hubs.
- Default: growth = volume CAGR; HKG/SGP/NLD/ARE flagged and excluded; RUS excluded (sanctions).
- **Given** I toggle "include hubs", **then** hubs appear with a ⚠ hub badge.
- **Given** I switch growth to "value", **then** a "price effect" column shows value CAGR − volume CAGR.

### US-07 · Entry-mode lens · Should · 5 pts · FR-1.7
**As** P1, **I want** markets where Lotte already produces locally to be labeled and scored on market attractiveness, **so that** India or Kazakhstan isn't penalised for low exports from Korea.
- Countries with a Lotte local plant (configurable list with sources) show a 🏭 "local production" badge.
- **Given** the lens is "Export from Korea", **then** local-production markets are shown separately, below a divider. **Given** "All entry modes", **then** they rank together, and the K-momentum pillar uses market-level demand instead of Korean exports.

### US-08 · Country profile · Must · 5 pts · FR-1.10
**As** P2, **I want** a country drawer with all indicators, trade history, tariffs, regulation summary and data coverage, **so that** I can do a deep-dive without leaving the tool.
- Shows each indicator's value, year, source and coverage badge; imputed values are badged.
- Shows Korea exports by category (2015–latest) and partner-reported imports from Korea; a mirror-discrepancy warning appears if they differ by more than ±30%.
- Shows the current tariff (with effective date) and the top 3 regulation items with links.

### US-09 · Forecast with uncertainty · Should · 8 pts · FR-1.11
**As** P3, **I want** a forecast with a 95% interval and a model-accuracy badge, **so that** I can judge the market's future without overtrusting it.
- History (solid) + forecast (dashed) + interval band for +1 to +3 years.
- A badge shows the backtest MAPE and whether the model beats the naïve baseline.
- **Given** fewer than 6 history points, **then** the panel shows "insufficient history", not a forecast.

### US-10 · TOPSIS cross-check · Should · 3 pts · FR-1.12
**As** P1, **I want** to see whether a second ranking method agrees, **so that** I can show the TOP3 isn't an artefact of one formula.
- Shows "TOPSIS agrees on 3/3 (or 2/3…)" with a list of differences.

### US-11 · Strategic-fit factor · Should · 3 pts · FR-1.13
**As** P1, **I want** an optional factor for Lotte's stated priority regions and brands, **so that** the ranking can reflect company strategy when I choose.
- Off by default. When on, it is labeled "business input (not market data)" and its weight is shown separately.

---

## Epic 2 — AI Agent & Recommendation Report

### US-12 · Ask in Korean or English · Must · 5 pts · FR-2.1, FR-2.2
**As** P1, **I want** to ask questions in Korean or English, **so that** I get answers in my working language.
- **Given** the UI language is KO, **when** I ask in either language, **then** the agent answers in Korean.
- Answers stream (first token ≤ 5 s warm).

### US-13 · Grounded answers only · Must · 8 pts · FR-2.3, FR-2.9
**As** P3, **I want** every number in an agent answer to come from data, **so that** I can trust it in a meeting.
- **Given** the agent's draft contains a number not present in any tool output, **then** the verifier rejects it and the agent rewrites (max 2), or answers without that number and notes the gap.
- Each answer has citations (source, year) that can be clicked through.
- Golden-set targets: numeric faithfulness ≥ 95%, citation precision ≥ 90%.

### US-14 · Regulation Q&A with citations · Must · 8 pts · FR-2.4
**As** P4, **I want** to ask "What do I need to sell ZERO cookies in Indonesia?", **so that** I know the requirements before planning a shipment.
- The answer cites document title, issuing body, date and URL. Example: PP 40/2026 moved the mandatory halal date for imported food to 18 Oct 2028.
- **Given** no relevant document is retrieved, **then** the agent replies "근거 없음 / no evidence found" and suggests official sources.

### US-15 · Agent drives the dashboard · Should · 5 pts · FR-2.5
**As** P1, **I want** to say "exclude markets with tariffs above 10% and focus on ice cream", **so that** I don't have to find the controls.
- The agent returns validated `ui_actions` and the UI applies them with a visible "Agent changed: category → Ice cream, max tariff → 10%" notice and an undo button.
- **Given** the actions fail validation, **then** nothing changes in the UI and the agent explains it couldn't apply them.

### US-16 · See what the agent did · Should · 2 pts · FR-2.6
**As** a judge, **I want** to see which tools the agent called, **so that** I can judge the quality of the AI design.
- A collapsible "에이전트가 수행한 분석" list shows tool name, key inputs and status.

### US-17 · Generate the TOP3 report · Must · 8 pts · FR-2.7
**As** P1, **I want** a one-click TOP3 report, **so that** I can share a review-ready document.
- Sections: executive summary, TOP3 table, per-country evidence (growth, trend, trade, entry), risks and regulations, recommended product lines and entry mode, method & weights used, P(TOP3), data sources.
- The report reflects the current category, weights and filters, and states them.
- All numbers pass the verifier.

### US-18 · Export to PDF / Markdown · Must · 3 pts · FR-2.8
**As** P1, **I want** PDF and Markdown exports, **so that** I can attach the report to emails or decks.
- "Export PDF" opens the print view and triggers `window.print()`: A4, page breaks between countries, charts sized correctly, citations as footnotes, UI controls hidden.
- "Download Markdown" saves a `.md` file with the same content.

---

## Epic 3 — Workflow Transformation & Monitoring

### US-20 · Sign in · Should · 3 pts · FR-3.3
**As** P2, **I want** to sign in with an email magic link or Google, **so that** my watchlist and alerts are saved.
- Dashboard and chat work without login (read-only). Watchlist, alerts and simulation require login.

### US-21 · Watchlist & preferences · Should · 3 pts · FR-3.3
**As** P2, **I want** to choose the countries and categories I watch, plus the alert sensitivity and email language, **so that** I only hear about what matters to me.
- Defaults: current TOP3, all categories, medium sensitivity, UI language, email on.

### US-22 · Daily refresh · Should · 8 pts · FR-3.1
**As** P1, **I want** the data refreshed daily, **so that** rankings don't go stale.
- Runs at 02:00 KST, can also be triggered manually. One failing source doesn't block the others. A run log is kept.
- The dashboard shows "data as of" per source.
- No Google Trends calls in automation.

### US-23 · Anomaly detection · Should · 8 pts · FR-3.2
**As** P2, **I want** the system to detect meaningful changes (trade spike/drop, TOP3 change, tariff/regulation change, FX swing), **so that** I react early.
- Each anomaly stores signal, country, category, period, value, baseline, z-score and source.
- Duplicates (same signal/country/period) are not re-alerted.
- Injected-spike recall ≥ 90% at medium sensitivity; replayed false alarms ≤ 1 per user per week.

### US-24 · Email brief · Should · 5 pts · FR-3.4
**As** P2, **I want** a short email when something on my watchlist changes, **so that** I don't have to check the dashboard daily.
- At most 1 email per user per day, sent only when ≥ 1 watched anomaly fires.
- Each item has: what changed, size of change, why it matters, source, and a deep link.
- The LLM writes the text and the verifier checks it; if either fails, a template is sent. Every email has an unsubscribe link.

### US-25 · Alert history · Should · 2 pts · FR-3.5
**As** P2, **I want** an in-app list of past alerts, **so that** I can review what happened.

### US-26 · Simulation sandbox · Should · 8 pts · FR-3.6
**As** a judge, **I want** to trigger a synthetic anomaly, **so that** I can see the whole monitoring loop without waiting for 02:00 KST.
- **Given** I'm signed in, **when** I run the simulation (default Vietnam, HS 1806, +45%), **then**:
  1. the ranking updates with before/after deltas;
  2. the forecast chart highlights the injected point as "SIMULATED";
  3. an alert with a SIMULATION badge appears;
  4. a `[SIMULATION]` email arrives in **my** inbox only.
- The overlay is session-only; reset clears it; it expires after 30 min.
- Rate limits: 5 simulations per hour and 3 simulation emails per day per user.
- No simulated data appears in real alerts, other users' views, or the evaluation metrics.

### US-19 · Time-savings evidence · Must · 3 pts · FR-3.7
**As** a judge, **I want** the time-savings claim backed by a stated baseline and a measurement, **so that** the business impact is credible.
- The README and proposal include the baseline assumption text and the measured median time from `eval/time_savings.py`.

---

## Epic 4 — Platform, Data & Reliability (enablers)

### US-30 · Warm-up when the backend is asleep · Must · 3 pts · FR-4.5
**As** a judge, **I want** a clear loading state when the backend is waking up, **so that** I don't think the app is broken.
- The loader "AI 엔진 준비 중 / AI Engine Waking Up" appears with per-component readiness, and a cached TOP3 is visible meanwhile.
- It recovers automatically when `/v1/health` reports ok. Chat is disabled until RAG and the LLM are ready.

### US-31 · Data provenance everywhere · Must · 5 pts · FR-4.1
**As** P1, **I want** every value to carry source, year and retrieval date, **so that** I can defend it.

### US-32 · Current tariffs with overrides · Must · 3 pts · FR-4.3
**As** P1, **I want** tariffs to reflect current policy (e.g. the US 15% reciprocal tariff), **so that** entry-ease scores are realistic.
- The tariff table records MFN, preferential (FTA) and override rates with effective dates and sources. The applied rate is the highest valid one.

### US-33 · Field-data ready · Should · 3 pts · FR-4.1
**As** the 본선 team, **we want** to load Lotte field data through the same schema, **so that** we can swap data without code changes.

---

## Could-have stories
- **US-27 · Concentration view (Could, 3 pts, MR-8):** show how the recommended TOP3 changes the share of exports going to the top 3 destinations.
- **US-28 · Competition context (Could, 3 pts, MR-6):** list Korean peers present in each market with a source.
- **US-29 · Tariff-impact tracking (Could, 5 pts):** monthly 관세청 data to show trade before and after a tariff change (e.g. USA after Aug 2025).

---

## Definition of Ready / Done
- **Ready:** the story has acceptance criteria, traces to an FR, has data available or a stub, and the UX sketch is agreed for UI stories.
- **Done:**
  - Acceptance criteria pass.
  - Tests written: unit or Playwright as appropriate.
  - KO/EN strings added.
  - Provenance shown for any new data.
  - Docs updated.
  - Deployed to preview.
