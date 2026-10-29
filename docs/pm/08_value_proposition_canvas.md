# 08 — Value Proposition Canvas

> Maps what B2B clients need (jobs, pains, gains) to what WellGTM offers (features, pain relievers, gain creators), and quantifies the value drivers.
> - Segment 1 is the design partner (Lotte Wellfood global business teams). Segment 2 is the Horizon 3 expansion segment.
> - Pains and gains are **hypotheses from desk research** until validated by interviews ([09 §6](09_market_research_report.md#6-client-research-programme)). Severity ratings are our current estimates.
> - The live ROI model with editable assumptions is in [`workbooks/WellGTM_market_research.xlsx`](workbooks/WellGTM_market_research.xlsx), sheet `ROI_Model`.

---

## 1. Canvas: Segment 1, Food manufacturer global business team (Lotte Wellfood)

```
┌──────────────────────── VALUE MAP (WellGTM) ────────────────────────┐   ┌────────────────────── CUSTOMER PROFILE ──────────────────────┐
│ PRODUCTS & SERVICES          │ GAIN CREATORS                        │   │ GAINS                          │ CUSTOMER JOBS               │
│ • Market ranking dashboard   │ • Review-ready TOP3 report in minutes│   │ • Defensible, explainable TOP3 │ • Choose TOP3 export        │
│   (weights, presets, P(TOP3))│ • Robustness shown (P(TOP3)) =       │   │ • Faster decisions             │   markets per category      │
│ • Category & entry-mode views│   confidence for the board           │   │ • One shared view across teams │ • Defend the choice to      │
│ • Country profiles w/ sources│ • One method & evidence base for     │   │ • Early warning on changes     │   executives                │
│ • Forecasts w/ intervals     │   strategy, sales, QA                │   │ • Fewer failed launches        │ • Monitor existing markets  │
│ • AI agent (KO/EN), tools +  │ • What-if in the meeting             │   │ • Diversify away from US/JP/CN │ • Check import rules before │
│   verifier + citations       │ • Product-line & entry-mode hints    │   │ • Own time spent on judgement, │   launch                    │
│ • Regulation RAG             │                                      │   │   not data wrangling           │ • Produce review decks      │
│ • TOP3 report (MD/PDF)       │ PAIN RELIEVERS                       │   │ PAINS                          │ • React to tariff/FX/rule   │
│ • Watchlists, daily refresh, │ • Automated, provenance-tagged data  │   │ • Weeks of manual data work    │   changes                   │
│   anomaly e-mail briefs      │ • Volume/hub/mirror corrections      │   │ • Numbers don't reconcile      │                             │
│ • Simulation sandbox         │   by default                         │   │ • Implicit weights → method    │                             │
│ • Excel/CSV export           │ • Explicit weights + sensitivity     │   │   challenged                   │                             │
│                              │ • Cited regulation answers +         │   │ • Studies stale on delivery    │                             │
│                              │   change alerts                      │   │ • Rules scattered/multilingual │                             │
│                              │ • Daily monitoring, 1 brief/day max  │   │ • Misleading nominal growth    │                             │
│                              │ • Grounded AI (no unsourced numbers) │   │ • Distrust of AI "black boxes" │                             │
└──────────────────────────────┴──────────────────────────────────────┘   └────────────────────────────────┴─────────────────────────────┘
```

### 1.1 Customer jobs
| Type | Job | Persona |
|---|---|---|
| Functional | Select and rank export markets per category for the annual and ad-hoc reviews | A, F |
| Functional | Size a market and understand its trend quickly when a distributor pitches it | B, C |
| Functional | Confirm import requirements (labeling, halal, registration) before planning a launch | D |
| Functional | Monitor existing markets for demand, tariff, regulation and FX changes | B, D, E |
| Functional | Produce a review-ready report with sources | A, C |
| Social | Be seen as rigorous and data-driven in front of leadership | A, C |
| Emotional | Feel confident a recommendation won't be overturned by a missed fact | A, D, F |
| Supporting | Keep data consistent across teams; answer ad-hoc data requests | C |

### 1.2 Pains (ranked by estimated severity)
| # | Pain | Severity | Evidence |
|---|---|:-:|---|
| P1 | Data assembly takes weeks; sources are fragmented | ●●●● | Baseline assumption ~45 business days ([PRD §5.3](../PRD.md#53-workflow-time-savings-baseline-assumption-epic-3)) |
| P2 | Recommendations are challenged because the weighting is implicit | ●●●● | The TOP3's third slot depends on weights ([03 §3](03_data_analysis.md#3-preliminary-screen-hypothesis-only)) |
| P3 | Policy changes are noticed late (tariffs, regulations) | ●●●● | US 15% tariff (Aug 2025); Indonesia halal date changed in Oct 2026 ([02 §6](02_market_analysis.md#6-market-access--regulation-key-candidates)) |
| P4 | Misleading data: nominal vs real growth, re-export hubs, mirror gaps | ●●● | Exports +7.7%/yr value vs ≈0% volume; NLD ranked #3 naïvely; mirror ratios 0.31–3.9 ([03](03_data_analysis.md)) |
| P5 | Regulations are scattered, multilingual and need verifying at the source | ●●● | Persona D |
| P6 | Studies are stale on delivery; consultants are costly | ●●● | Persona F |
| P7 | Distrust of AI-generated numbers | ●●● | General enterprise AI adoption barrier; Persona A/D quotes |
| P8 | Ad-hoc data requests eat analyst time | ●● | Persona C |
| P9 | Export concentration risk is not visible | ●● | USA+JPN+CHN = 57% ([03 F2](03_data_analysis.md#f2-exports-are-concentrated-the-usa-japan-and-china-take-57)) |

### 1.3 Gains
| Type | Gain | Persona |
|---|---|---|
| Required | Accurate numbers with sources | All |
| Required | Korean-language support | A, B, D |
| Expected | A ranking that can be adjusted to strategy | A, F |
| Expected | Exportable report and data (PDF, Excel) | A, C |
| Desired | Robustness or confidence level for each recommendation | A, F |
| Desired | Proactive alerts filtered to their markets | B, D, E |
| Desired | Product-line and entry-mode suggestions | A, F |
| Unexpected | Agent that changes the dashboard on request | A |
| Unexpected | Simulation of "what if a market spikes?" | F |

### 1.4 Fit map: pain → reliever → feature → proof
| Pain / gain | Pain reliever / gain creator | Feature (PRD ref) | How we prove it |
|---|---|---|---|
| P1 Weeks of data work | Automated pipeline with provenance | FR-4.1, FR-3.1 | Measured end-to-end time (`eval/time_savings.py`) |
| P2 Method challenged | Explicit weights, presets, P(TOP3), TOPSIS cross-check | FR-1.1–1.3, FR-1.12 | Demo: change weights, show which countries stay robust |
| P3 Late awareness | Daily refresh + anomaly detection + email brief | FR-3.1–3.4 | Simulation sandbox; injected-spike recall ≥ 90% |
| P4 Misleading data | Volume growth, hub exclusion, mirror warnings by default | FR-1.5, FR-1.6, FR-1.10 | Before/after ranking comparison ([03 fig 5](figures/fig5_top3_sensitivity.png)) |
| P5 Scattered regulations | Regulation RAG with dated citations; "no evidence" fallback | FR-2.4 | RAG hit@5 ≥ 85%; citation precision ≥ 90% |
| P6 Stale studies | Continuous monitoring; reproducible reports on demand | FR-2.7, FR-3.1 | "Data as of" dates; daily job success ≥ 95% |
| P7 AI distrust | Tools-only facts + verifier + tool trace | FR-2.3, FR-2.6 | Numeric faithfulness ≥ 95% (eval report) |
| P8 Ad-hoc requests | Self-service profiles, agent Q&A, Excel export | FR-1.10, FR-2.2 | Requests answered in minutes |
| P9 Concentration | Concentration view | US-27 (*Could*) | Show TOP3 effect on concentration |
| Gain: confidence level | P(TOP3), coverage badges, forecast intervals | FR-1.3, FR-1.11 | Visible on every card |
| Gain: product/entry hints | Category view, entry-mode lens | FR-1.4, FR-1.7 | Report section "recommended product lines and entry mode" |

**Fit check:**
- Every ●●●● pain has a Must or Should feature and a measurable proof.
- P9 is covered only by a Could feature. It is acceptable for 예선 and becomes a candidate for Horizon 2.

---

## 2. Canvas: Segment 2, Export-support organisations (Horizon 3)

| Customer profile | Value map |
|---|---|
| **Jobs:** advise many SME exporters on target markets; allocate export-support budgets (e.g. vouchers); publish market information | **Products:** multi-tenant ranking for many product categories; white-label reports; aggregate monitoring |
| **Pains:** advice is one-off and labour-intensive; SMEs can't interpret raw trade data; information spread across many reports | **Pain relievers:** standardised, explainable rankings per SME product; automated report generation; regulation Q&A at scale |
| **Gains:** more SMEs served per advisor; measurable programme outcomes; consistent methodology | **Gain creators:** usage analytics; outcome tracking; KO/EN outputs for SMEs |

> Segment 2 is a **hypothesis** for later horizons. Market research found that aT (ChaTi) and KOTRA (AI 수출비서) are building their own AI tools, so this segment is more likely a **partner or data source** than a buyer ([09 §3.4](09_market_research_report.md#34-competitive-implications)).

---

## 3. Value drivers

| Driver | Mechanism | Metric | Type |
|---|---|---|---|
| **Reduced operational overhead** | Automates data collection, reconciliation, charting and first-draft reports | Analyst days saved per study; ad-hoc request hours saved | Hard cost (base ROI) |
| **Lower external research spend** | Fewer or smaller consulting studies for first-pass screening | Consulting spend avoided | Hard cost (base ROI) |
| **Faster time-to-decision** | Weeks → minutes for the first pass | Time to defensible TOP3 | Speed |
| **Better decision quality** | Corrected data, explicit trade-offs, robustness | Share of decisions with a cited report; fewer reversed decisions | Risk/quality (upside) |
| **Risk reduction** | Early regulatory and tariff awareness | Compliance surprises avoided; failed-entry probability | Risk (upside) |
| **Revenue upside** | Better market choice and timing → share gains in priority markets | Share gain in SAM (each +0.1pp ≈ US$33M of category imports, [02 §8](02_market_analysis.md#8-market-sizing-tam--sam--som)) | Growth (upside, not attributed) |

---

## 4. Illustrative ROI model (base case = hard cost savings only)

> ⚠️ **All inputs are placeholder assumptions** for discussion. Replace them with Lotte Wellfood figures during 본선. The Excel version recalculates automatically.

| Input | Assumption | Note |
|---|---:|---|
| Market-prioritisation studies per year | 4 | Annual review + ad-hoc requests |
| Analyst effort per study, baseline (days) | 45 | PRD baseline assumption |
| Analyst effort per study with WellGTM (days) | 5 | Review, validation, local input remain manual |
| Fully loaded analyst cost per day (₩) | 500,000 | Placeholder |
| Ad-hoc data requests per month | 20 | Placeholder |
| Hours saved per ad-hoc request | 3 | Placeholder |
| External consulting studies avoided per year | 1 | Placeholder |
| Cost per consulting study (₩) | 100,000,000 | Placeholder |
| Annual cost of WellGTM (₩) | 60,000,000 | Placeholder SaaS price / internal run cost |

| Output | Formula | Value (₩) |
|---|---|---:|
| Study effort savings | 4 × (45 − 5) × 500,000 | 80,000,000 |
| Ad-hoc request savings | 20 × 12 × 3 × (500,000 ÷ 8) | 45,000,000 |
| Consulting avoided | 1 × 100,000,000 | 100,000,000 |
| **Total annual benefit (base)** | | **225,000,000** |
| Annual cost | | 60,000,000 |
| **Net benefit** | | **165,000,000** |
| **ROI** | net ÷ cost | **275%** |
| **Payback** | cost ÷ (benefit ÷ 12) | **≈ 3.2 months** |

**Upside scenarios (not included in base ROI):**

| Scenario | Assumption | Expected annual value (₩) |
|---|---|---:|
| Avoided failed market entry | 1 new-market entry per year; cost of a failed entry ₩1B (listing fees, marketing, write-offs); WellGTM lowers failure probability by 10pp | 100,000,000 |
| Revenue share gain | +0.1pp share in SAM ≈ US$33M category imports; WellGTM attribution 5%; margin 10% | ≈ 0.165M US$ ≈ ₩231M at ₩1,400/US$ |

> The base case uses cost savings only, because they are easiest to verify. Revenue upside is shown to explain why the decision matters; we don't attribute it to the tool in claims.

---

## 5. Value proposition statements (for the proposal)
- **For strategy managers:** "A defensible TOP3 export-market recommendation, with sources and confidence, in minutes instead of weeks."
- **For export sales:** "Know what changed in your markets this week, and whether it matters, before your distributor tells you."
- **For regulatory/QA:** "Import requirements with the regulation number, issuing body and date, plus an alert when they change."
- **For executives:** "Three markets, how sure we are, and what would change the answer, on one page."
- **For analysts:** "One trusted, sourced data layer instead of quarterly spreadsheet rebuilds."
