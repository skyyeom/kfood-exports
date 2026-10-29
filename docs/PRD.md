# WellGTM — Product Requirements Document (PRD)

| | |
|---|---|
| **Product** | WellGTM: K-Food Export Market Intelligence Agent for Lotte Wellfood |
| **Challenge** | Lotte AX Challenge 2026: 롯데웰푸드 K-푸드 수출 유망국가 발굴 |
| **Stage** | 예선 (proposal + working demo). Designed so 본선 field data can be added without changes |
| **Status** | Draft v1 for review |
| **Owner** | PM: Sky Yeom |
| **Related docs** | [Product vision](pm/00_product_vision.md) · [Problem discovery](pm/01_problem_discovery.md) · [Market analysis](pm/02_market_analysis.md) · [Data analysis](pm/03_data_analysis.md) · [User stories](pm/04_user_stories.md) · [Roadmap](pm/05_roadmap.md) · [Metrics & evaluation](pm/06_metrics_and_evaluation.md) · [Decision & risk log](pm/07_decision_risk_log.md) · [Value proposition canvas](pm/08_value_proposition_canvas.md) · [Market research](pm/09_market_research_report.md) · [Personas](pm/10_user_personas.md) · [Product roadmap](pm/11_product_roadmap.md) |

---

## 1. TL;DR
Lotte Wellfood wants to grow its overseas revenue share from ~28.6% to 35% by 2028, and has made Pepero its first global mega brand. Choosing *where* to push exports is currently a slow, manual, opaque process that can mislead. The causes:
- Nominal growth hides flat volumes.
- Re-export hubs look like great markets.
- Tariffs and regulations change often.

**WellGTM** is a web dashboard with an AI agent that:
1. **Ranks** ~30 countries on transparent, adjustable criteria (market growth, consumer trends, trade status, entry ease), per category, and shows **how robust the TOP3 is**.
2. **Explains** every recommendation with cited evidence and writes a **TOP3 report**.
3. **Answers questions** in Korean or English, grounded in data and regulations, and can **drive the dashboard**.
4. **Monitors** markets daily and **emails** each user a brief when something they watch changes.

---

## 2. Problem & evidence
| Evidence | Source |
|---|---|
| Korea's category exports (HS 1704/1806/1905/2105) grew **+7.7%/yr in value but ≈0% in volume** (2020–25). Only ice cream grew in real terms (+13.1%/yr). | [03 F1](pm/03_data_analysis.md) |
| A naïve screen ranks the **Netherlands #3**, an artefact of re-export hubs. | [03 F6](pm/03_data_analysis.md) |
| Partner vs Korea-reported statistics differ by up to **3×** (e.g. the Philippines reports 31% of what Korea says it shipped). | [03 F4](pm/03_data_analysis.md) |
| The **third TOP3 slot changes with weights** (Philippines vs Canada vs India), so the "answer" depends on business priorities. | [03 §3](pm/03_data_analysis.md) |
| Material policy shocks: 15% US tariff (Aug 2025); Indonesia halal deadline moved to Oct 2028 (PP 40/2026, Oct 2026). | [02 §6](pm/02_market_analysis.md) |
| Lotte produces locally in India, Kazakhstan, Russia, Pakistan and Myanmar, and is exiting China manufacturing. Korea-export-only metrics misjudge these markets. | [02 §3.2](pm/02_market_analysis.md) |
| Assumed manual baseline: ~45 business days per market-prioritisation study (see §5.3). | [01 §3](pm/01_problem_discovery.md) |

---

## 3. Goals & non-goals

### 3.1 Goals
| # | Goal | Measured by (§5) |
|---|---|---|
| G1 | Produce a **defensible TOP3** of export markets, per category, with evidence | TOP3 stability, evidence coverage, user and judge acceptance |
| G2 | Make the method **transparent and adjustable** | Weight changes re-rank in ≤500ms; every score can be broken down |
| G3 | Provide an **accurate, grounded AI agent** | Numeric faithfulness ≥ 95%, citation precision ≥ 90% |
| G4 | Turn a one-off study into **continuous monitoring** | Daily job success ≥ 95%; alert precision on replayed history |
| G5 | **Compress first-pass screening from weeks to minutes** | Median end-to-end run < 5 min (measured) |

### 3.2 Non-goals (예선)
- Final investment decisions. WellGTM supports first-pass screening; people make the decision.
- Paid data sources (Euromonitor, Nielsen). Adapters may come later.
- SKU-level demand forecasting or pricing optimisation.
- Interactive world map (stretch goal only).
- Lotte internal system integration (ERP and sales data). Planned for 본선 through the common schema.
- Mobile-native app (responsive web only).

---

## 4. Users
| Persona | Primary jobs | Priority |
|---|---|---|
| **P1 Global Market Strategy Manager** | Rank and defend the TOP3; produce the review report | **Primary** |
| P2 Export Sales Manager | Country × category deep-dives; alerts for their countries | Secondary |
| P3 Executive | One-page TOP3 and confidence level | Secondary (report consumer) |
| P4 Regulatory / QA | Cited regulation answers; change alerts | Secondary |
| P5 Brand manager | Category and trend views | Tertiary |
| Judges | Quick, reliable demo at any time | Critical for 예선 |

Details: [01 §2](pm/01_problem_discovery.md).

---

## 5. Success metrics

### 5.1 North-star metric
**Time to a defensible TOP3:** time from opening WellGTM to an exported TOP3 report with cited evidence. Target: **< 5 minutes (median)**.

### 5.2 KPIs & guardrails
| Type | Metric | Target (예선) | How measured |
|---|---|---|---|
| Outcome | Time to defensible TOP3 | < 5 min median | `eval/time_savings.py` (scripted run, N ≥ 10) |
| Quality | Agent **numeric faithfulness** (numbers traceable to tool outputs) | ≥ 95% | Golden set + verifier logs |
| Quality | **Citation precision** (cited source supports the claim) | ≥ 90% | Golden set, manual + automated check |
| Quality | Tool-selection accuracy | ≥ 90% | Golden set |
| Quality | Correct refusal on no-evidence questions | ≥ 90% | Golden set (out-of-scope items) |
| Quality | RAG retrieval hit@5 | ≥ 85% | Labeled query set |
| Quality | Forecast: beats naïve baseline (MAPE) | in ≥ 60% of series | Rolling-origin backtest |
| Quality | Anomaly detector recall on injected spikes | ≥ 90% at medium sensitivity | Synthetic injection test |
| Guardrail | Alert false-alarm rate on replayed history | ≤ 1 alert per user per week (medium) | Historical replay |
| Guardrail | Slider → re-rank latency | p95 ≤ 500 ms | Playwright timing |
| Guardrail | Daily job success rate | ≥ 95% | GitHub Actions history |
| Guardrail | `ui_actions` validation failures that break the UI | 0 | Fuzz tests + error boundary |
| Guardrail | Infra cost | US$0 (free tiers) | — |

### 5.3 Workflow time-savings baseline assumption (Epic 3)
> "Baseline assumes a manual cross-border market research process requires 15 business days for macroeconomic data aggregation, 20 business days for regulatory manual parsing via local embassies/KOTRA, and 10 business days for time-series export modeling. WellGTM automates data compilation via async pipelines and regulatory checking via RAG, compressing execution latency."

- The **45 business days** total is an **assumption**. We will validate it with Lotte staff if possible (open question Q4) and label it as an assumption wherever it appears.
- The "< 5 minutes" figure is **measured, not asserted**, using the scripted end-to-end run.
- Scope of the claim: **first-pass screening and evidence assembly**. Final decisions still need human review and local validation.

---

## 6. Product principles
1. **Evidence first.** Every number has a source, a year and a retrieval date. The agent never states a number it did not get from a tool.
2. **Show uncertainty.** Show TOP3 probability, data coverage and forecast intervals, not just point values.
3. **Correct for known biases by default.** Use volume over value, exclude hubs, prefer Korea-reported flows. Users can always toggle the corrections off.
4. **Human in control.** Users set the weights; the agent proposes changes and the user applies them.
5. **Works for judges at any time.** Handle cold starts, provide a simulation sandbox, and keep cached data.
6. **Bilingual.** Korean and English are equal citizens.

---

## 7. Scope (MoSCoW)

| Priority | Capability |
|---|---|
| **Must** | Data pipeline with provenance (Comtrade, World Bank, Korea-reported exports, tariffs); multi-criteria scoring with sliders and presets; TOP3 cards with reason packs; sensitivity (P(TOP3)); category filter; hub/sanction handling; country profile; agent chat with tools + verifier + citations; regulation RAG; TOP3 report (Markdown + PDF via print); KO/EN; cold-start handling; evaluation suite |
| **Should** | TOPSIS cross-check; forecast with backtest and intervals; entry-mode lens; strategic-fit factor; Google Trends snapshot pillar; login + watchlists; daily refresh; anomaly detection; email briefs; simulation sandbox |
| **Could** | Competition context per market; concentration/diversification view; 관세청 monthly data for tariff-impact tracking; Taiwan data source |
| **Won't (예선)** | World map; paid data; Lotte internal data; SKU-level forecasting; mobile app |

> Monitoring features are "Should" rather than "Must" because the core challenge asks for TOP3 plus evidence. Monitoring is what makes the product useful beyond a one-off study.

---

## 8. Solution overview

### 8.1 Key user flows
1. **Screen & rank (P1):** open dashboard → choose category and preset ("Scale" / "Growth-entry" / custom) → adjust weights → see TOP3 with P(TOP3) and reason chips → open a country profile → export the report.
2. **Ask the agent (P1, P2, P4):** "Why is the Philippines above Malaysia for ice cream?" → the agent calls the ranking and profile tools and answers with citations. Then "Exclude markets with tariffs above 10%" → the agent proposes a filter → the UI applies it.
3. **Regulation check (P4):** "What do I need to sell ZERO cookies in Indonesia?" → RAG answer citing PP 40/2026, BPJPH and BPOM sources, or "근거 없음" if no evidence is found.
4. **Monitor (P2):** set a watchlist (PHL, MYS · ice cream) → receive an email brief when a monitored signal changes → click through to evidence.
5. **Judge demo:** open the site → warm-up loader → dashboard → run the simulation (+45% Vietnam) → see the re-rank, chart highlight, agent alert and email.

### 8.2 Scoring model (summary)
- **Pillars:** market growth (volume-based), market size, consumer trends, K-momentum (Korea-reported exports), entry ease (tariff, LPI, regulatory burden), optional strategic fit.
- **Method:** indicators are normalised with winsorised min-max (logged for size), averaged into pillars, then combined with a weighted sum. TOPSIS runs as a cross-check.
- **Robustness:** Monte Carlo weight perturbation (±20%) plus random weights give P(TOP3).
- **Output per country:** score, rank, P(TOP3), pillar breakdown, a reason pack (top 3 drivers, weakest factor, cited facts) and data-coverage badges.

### 8.3 Architecture (summary)
- **Frontend:** Next.js on Vercel.
- **Backend:** FastAPI + LangGraph + Chroma on Hugging Face Spaces (Docker).
- **Auth and storage:** Supabase (Auth, Postgres, Storage).
- **Automation:** GitHub Actions daily job.
- **Email:** Brevo SMTP.
- **LLM and embeddings:** the LLM provider is pluggable; embeddings run locally (multilingual).

Full detail is in the engineering plan.

---

## 9. Functional requirements
Requirement IDs link to user stories in [04_user_stories.md](pm/04_user_stories.md). DR = data requirement ([03](pm/03_data_analysis.md)), MR = market requirement ([02](pm/02_market_analysis.md)).

### Epic 1 — Market Screening & Ranking
| ID | Requirement | Traces |
|---|---|---|
| FR-1.1 | Rank candidate countries on pillar scores using user-adjustable weights. Recompute in ≤ 500 ms p95 | G2 |
| FR-1.2 | Provide presets: "Scale markets", "Growth/entry markets", "Balanced", plus custom | DR-6 |
| FR-1.3 | Show P(TOP3) for every country under weight uncertainty | DR-5 |
| FR-1.4 | Category filter (HS 1704/1806/1905/2105/all) that re-scores everything | DR-8, MR-3 |
| FR-1.5 | Growth uses volume by default; a toggle switches to value; the price effect is shown | DR-1, DR-9 |
| FR-1.6 | Hubs (HKG, SGP, NLD, ARE) are flagged and excluded by default; sanctioned markets are excluded by default; both can be toggled | DR-2 |
| FR-1.7 | Entry-mode lens: label "local production" markets and score them on market attractiveness (Korean-export momentum is not penalised) | DR-7, MR-1 |
| FR-1.8 | Hard filters: max tariff, region, minimum market size | — |
| FR-1.9 | TOP3 cards: score, rank change vs default, P(TOP3), top drivers, weakest factor, sources | G1 |
| FR-1.10 | Country profile: indicators with year, source and coverage; Korea exports by category; mirror discrepancy warning (>±30%); tariff and regulation summary; competitors present | DR-3, DR-4, MR-6 |
| FR-1.11 | Forecast panel: history + forecast + 95% interval for +1 to +3 years; backtest accuracy badge | G1 |
| FR-1.12 | TOPSIS cross-check: show whether TOPSIS agrees with the weighted-sum TOP3 | — |
| FR-1.13 | Optional strategic-fit factor (Lotte's priority regions/brands), off by default and clearly labeled as a business input | MR-2 |

### Epic 2 — AI Agent & Recommendation Report
| ID | Requirement | Traces |
|---|---|---|
| FR-2.1 | Chat in KO/EN; replies in the active UI language | — |
| FR-2.2 | The agent uses typed tools only: rankings, country profile, compare, forecast, regulation search, set dashboard state, generate report | G3 |
| FR-2.3 | **No ungrounded numbers:** a verifier checks every number and citation against tool outputs; failure → rewrite (max 2) → safe fallback | G3 |
| FR-2.4 | Regulation answers cite source title, date and URL; if retrieval finds nothing relevant, answer "근거 없음 / no evidence found" | G3 |
| FR-2.5 | The agent can propose dashboard changes (weights, filters, focus country), sent as validated `ui_actions` and applied with a visible change notice | G2 |
| FR-2.6 | Show the tool-call trace ("what the agent did"), collapsible | AI 역량 |
| FR-2.7 | TOP3 report: executive summary, TOP3 table, per-country evidence (growth, trend, trade, entry), risks and regulations, recommended product lines and entry mode, method, and data sources | G1 |
| FR-2.8 | Export: Markdown download and PDF via browser print (A4 layout, citations as footnotes) | — |
| FR-2.9 | The agent never claims certainty it does not have: it mentions P(TOP3) and data gaps when relevant | Principle 2 |

### Epic 3 — Workflow Transformation & Monitoring
| ID | Requirement | Traces |
|---|---|---|
| FR-3.1 | Daily refresh (02:00 KST) of all automated sources; idempotent; per-source failure isolation; run log. Google Trends is excluded (static snapshot) | G4 |
| FR-3.2 | Anomaly detection: trade spike/drop, TOP3 change, tariff/regulation document change, FX swing (Trends only on manual snapshot refresh) | G4 |
| FR-3.3 | Login (magic link / Google). Watchlist of countries × categories; sensitivity; email language; on/off | G4 |
| FR-3.4 | Email brief only when a watched signal fires; max 1 per user per day; LLM-written with the verifier, template fallback; unsubscribe link | G4 |
| FR-3.5 | In-app alert history with links to evidence | G4 |
| FR-3.6 | **Simulation sandbox:** inject a synthetic anomaly (default +45% Vietnam, HS 1806) into a session-only overlay → re-rank, chart highlight, agent alert, `[SIMULATION]` email to self; reset; rate-limited | Judges |
| FR-3.7 | Time-savings measurement script and report; baseline assumption displayed in the README and proposal | G5 |

### Epic 4 — Platform & Data Foundation (enabler)
| ID | Requirement | Traces |
|---|---|---|
| FR-4.1 | Common schema (`country_indicators`, `trade_flows`) with `source`, `retrieved_at`, `unit`, `year`, `imputed` flags; 본선 field data loads through the same schema with `source=lotte_field` | DR-4 |
| FR-4.2 | Korea-reported exports are the primary measure for Korea flows; partner-reported data is context | DR-3 |
| FR-4.3 | Tariff table supports current overrides (e.g. the US 15% reciprocal tariff) with effective dates and sources | MR-4 |
| FR-4.4 | Taiwan: alternative source or a "partial data" badge | DR-10 |
| FR-4.5 | `/v1/health` with component readiness; frontend warm-up loader; cached TOP3 fallback | Judges |

---

## 10. Non-functional requirements
| Area | Requirement |
|---|---|
| Performance | Re-rank ≤ 500 ms p95; first agent token ≤ 5 s (warm); report generation ≤ 60 s |
| Availability | The demo works from a cold start: loader shown immediately, usable within ~120 s; cached TOP3 visible meanwhile |
| Accuracy | See §5.2 quality targets |
| Robustness | Malformed LLM output never breaks the UI (validation pipe + error boundary) |
| Security & privacy | Restricted CORS; Supabase row-level security; secrets only in platform secret stores; no Lotte confidential data in 예선; public data only |
| i18n | Full KO/EN UI and agent output; locale-aware number formatting |
| Accessibility | Keyboard-navigable controls; chart colours safe for colour-blind users; text alternatives for charts in the report |
| Cost | Runs on free tiers (Vercel, HF Spaces, Supabase, Brevo, GitHub Actions, free LLM tier) |
| Maintainability | Reproducible pipeline; CI tests; pluggable LLM, embeddings and email |

---

## 11. Data requirements
| Dataset | Source | Refresh | Notes |
|---|---|---|---|
| Category imports by country (World, from Korea) | UN Comtrade | Daily check, annual data | Hubs flagged |
| Korea exports by destination × HS | UN Comtrade (Korea-reported); 관세청 (monthly, *Could*) | Daily check | Primary measure of K-momentum |
| Macro indicators | World Bank WDI | Daily check | GDP pc, growth, population, urbanisation, consumption, inflation |
| Logistics | World Bank LPI | Static (2023) | Coarse proxy |
| Tariffs | WITS/TRAINS + manual overrides | Daily check + manual | Effective dates |
| Consumer trends | Google Trends (one-off local snapshot); Hallyu indicators | Manual | As-of date displayed |
| FX | open.er-api / Frankfurter | Daily | For FX-swing alerts |
| Regulation corpus | Public regulator and trade-body documents (FDA, GACC, BPJPH, JAKIM, FSSAI, GSO, EU Novel Food, KOTRA/aT summaries) | Monitored URLs, daily hash check | Metadata: source URL, title, country, date |

---

## 12. AI requirements & guardrails
- **Models:** pluggable chat LLM (free tier by default); local multilingual embeddings.
- **Grounding:** tools-only facts; the verifier checks numbers and citations; RAG answers require a cited chunk.
- **Structured output:** typed SSE events. `ui_actions` only in the validated final event. Validation chain: json-repair → Pydantic (strict) → rewrite loop → safe drop. The client re-validates with zod.
- **Safety:** no investment guarantees; disclaim simulation data; refuse out-of-scope requests politely.
- **Evaluation:** golden question set (KO/EN, 30–50 items), RAG hit@k, fuzz tests, backtests. Results are published in `eval/reports/`.

---

## 13. Assumptions, dependencies, risks (summary)
See the [decision & risk log](pm/07_decision_risk_log.md) for the full register.

- **Key assumptions:** P1 is the primary user; the 45-day baseline holds; public data is adequate for the 예선; free tiers are sufficient.
- **Dependencies:** Comtrade preview API limits; free LLM rate limits; Brevo sender verification; Supabase project.
- **Top risks:**
  - The TOP3 is sensitive to weights. Mitigation: P(TOP3) and presets.
  - Data gaps (Taiwan, Vietnam 2024+). Mitigation: badges and Korea-reported data.
  - LLM hallucination. Mitigation: verifier and evaluation set.
  - Free-tier cold starts. Mitigation: warm-up and cached TOP3.

---

## 14. Release plan
Milestones without dates; detail in the [roadmap](pm/05_roadmap.md).

| Milestone | Content | Exit criteria |
|---|---|---|
| **M0 Discovery** ✅ | Problem discovery, market analysis, data analysis, PRD, stories | Documents reviewed |
| **M1 Data foundation** | Schema, pipeline, provenance, Trends snapshot, tariff table | Indicator tables reproduce the analysis numbers |
| **M2 Scoring MVP** | Scoring, presets, sensitivity, reason packs, forecast | Unit tests pass; preliminary TOP3 reproduced |
| **M3 API + UI MVP** | FastAPI + Next.js dashboard, KO/EN, warm-up | Slider p95 ≤ 500 ms; deployed preview |
| **M4 Agent + report** | Tools, verifier, RAG, chat, report/print | Golden-set targets met |
| **M5 Monitoring** | Auth, watchlists, daily job, anomalies, email, simulation | End-to-end simulation demo works |
| **M6 Submission** | Evaluation reports, time-savings measurement, proposal, demo video | All §5 metrics reported |

---

## 15. Open questions
| # | Question | Owner | Status |
|---|---|---|---|
| Q1 | Primary user: global strategy vs export sales? | PM | Open: assume P1 |
| Q2 | Does "export" include production at overseas plants? | PM | Open: entry-mode lens covers both |
| Q3 | Which categories are in scope beyond confectionery and ice cream? | PM | Open: 4 HS codes, configurable |
| Q4 | Can the 45-day baseline be validated? | PM | Open |
| Q5 | What field data will 본선 provide? | PM | Open: common schema |
| Q6 | Which free LLM do we demo with (Gemini vs Groq)? | Eng | Open: decide in M4 by eval score and rate limit |
