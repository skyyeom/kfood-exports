# 09 — Market Research Report (B2B)

> **Scope:** B2B market trends, competitor and alternative analysis, and client insights for WellGTM, an AI service that ranks, explains and monitors export markets for food manufacturers.
> **Date:** 2026-10-29 · **Inputs:** desk research (sources in §8), our trade-data analysis ([03](03_data_analysis.md)), K-food market analysis ([02](02_market_analysis.md)).
> **Client-interview status:** ⚠️ **No client interviews or surveys have been run yet.** §5 lists the hypotheses to validate and the evidence so far. §6 gives the ready-to-run research programme (interview guide, Microsoft Forms survey, Excel analysis workbook). This report will be updated with real interview insights; none are invented here.

**Companion files**
- 📊 [`workbooks/WellGTM_market_research.xlsx`](workbooks/WellGTM_market_research.xlsx): country data, TAM/SAM/SOM, competitors, trends, ROI model, interview tracker, survey analysis (auto-calculating), insight synthesis.
- 📝 [`workbooks/WellGTM_client_survey_for_MS_Forms.docx`](workbooks/WellGTM_client_survey_for_MS_Forms.docx): upload in Microsoft Forms → *Quick import*.

---

## 1. Executive summary
1. **The gap is real but narrow.** No product reviewed combines all four capabilities WellGTM targets (*ranked + explainable + continuously monitored + regulation Q&A*) for a specific manufacturer's products. Each capability exists somewhere:
   - ITC's Export Potential Map ranks markets with a published method, but generically.
   - Tridge and the shipment-data platforms monitor continuously.
   - Tridge's Eye AI Chat and aT's ChaTi give cited AI answers.
   - **WellGTM's differentiation is the combination, made specific to one manufacturer.**
2. **Free public AI tools are arriving in Korea.**
   - aT's **ChaTi** (cited RAG over ~80,000 KATI documents) has been in full service since **Dec 2025** and aims to become a "K-Food export AI agent".
   - KOTRA announced an **"AI 수출비서"** (market and buyer recommendations, strategy reports) for 2026.
   - WellGTM should not compete on generic Q&A. It should compete on **company-specific ranking, robustness, data corrections and monitoring**, and use public data as inputs.
3. **Demand drivers are evidenced:**
   - Tariff volatility: about two-thirds of trade professionals use trade-lane analysis tools; 48% are investing in new tech for tariff workload.
   - Rising AI adoption in CPG: 42% → 71% of CPG leaders adopted AI in at least one function (2023 → 2024).
   - K-food export growth.
4. **Buyers are sceptical about ROI.** Only 16.5% of retail/CPG executives can quantify AI ROI, and only ~7% of organisations have fully scaled AI. Sell with **measured time savings and an ROI model**, and make explainability the trust mechanism.
5. **Market sizing must be bottom-up.** There is no standard "market intelligence software" category. The closest verified adjacent market is trade compliance software (~US$1.95B in 2025, ~12% CAGR).
6. **Export vouchers are not a confirmed funding path for SaaS.** The 14 voucher categories have no software line item. Don't claim eligibility.

---

## 2. B2B market trends

| # | Trend | Evidence | Implication for WellGTM |
|---|---|---|---|
| T1 | **No clean category; adjacent markets growing ~12%/yr** | Trade compliance software US$1.73B (2024) → US$1.95B (2025) → US$3.09B (2029), CAGR ~12% [B1]. BI software estimates differ 3–5× between firms (US$40.1B 2025, Grand View; US$47.5B 2026, Precedence) [B2, B3] | Size the opportunity bottom-up (target accounts × price); avoid inflated BI totals |
| T2 | **AI is widespread but rarely scaled** | 88% of organisations use AI in ≥1 function; ~7% fully scaled; 39% report any EBIT impact [B4]. Only 5% are "future-built"; 60% see minimal value [B6] | Position as a focused, outcome-measured use case, not a general AI platform |
| T3 | **CPG is adopting quickly, but immature** | CPG AI adoption 42% (2023) → 71% (2024); 56% use GenAI regularly; "no CPG player has truly scaled" [B5] | Design-partner → pilot → rollout path (roadmap H1→H2) fits buyer maturity |
| T4 | **ROI scepticism** | 75% of retail/CPG execs call AI a top priority; 16.5% can quantify ROI [B7, *date precision unverified*] | Ship the ROI model ([08 §4](08_value_proposition_canvas.md#4-illustrative-roi-model-base-case--hard-cost-savings-only)) and measured time savings |
| T5 | **Agentic AI is rising** | AI agents ≈17% of AI value in 2025 → 29% by 2028 (projected) [B6] | The agent should *do* things (rank, filter, write the report), not just chat |
| T6 | **Tariff volatility drives tooling** | ~2/3 use trade-lane analysis tools; >1/2 use risk-identification tools; ~75% changing sourcing [B8]. 48% investing in new tech for tariff workload; 51% use GenAI for trade-policy scenario modelling [B9] | Monitoring, tariff overrides, what-if analysis and the simulation sandbox meet real demand |
| T7 | **Tariff levels at historic highs** | US effective tariff 16.8% (Nov 2025), highest since 1935 [B10, *re-verify*]; Korea faces a 15% baseline since Aug 2025 [02 R1] | Tariff pillar must reflect current overrides with dates |
| T8 | **Incumbents add GenAI on proprietary content** | Euromonitor Passport AI (Sep 2024) and Passport Connect/MCP (Oct 2026); Statista Research AI + MCP (2024–25); Mintel Leap/Spark [C1–C3] | Citations are becoming standard; our edge must be ranking + corrections + monitoring |
| T9 | **Public-sector AI in Korea** | aT ChaTi (Dec 2025; national innovation award Oct 2026); KOTRA "AI 수출비서" (2026 first phase) [K1, K2] | Partner with or build on public data; avoid competing on free generic Q&A |
| T10 | **K-food exports keep growing** | Agri-food US$10.41B (2025); biscuits & confectionery US$770M (2024, +17.4%); ice cream US$111M (2025, +21.6%) [02 S1–S7] | A growing base of exporters need better market selection |
| T11 | **Nominal growth misleads** | Korea's category exports +7.7%/yr value vs ≈0% volume (2020–25); chocolate imports +21.7% value / −13.3% volume in 2025 [03] | Data corrections are a differentiator vs raw-data tools |

---

## 3. Competitor & alternative analysis

### 3.1 Landscape
| Alternative | Type | Target customer | Core offering | AI features | Pricing | Main gap vs WellGTM |
|---|---|---|---|---|---|---|
| **Euromonitor Passport** | Syndicated research | Enterprise strategy/insight teams | 210-country category data, field research | Passport AI (RAG on own content, Sep 2024); Connect/MCP (Oct 2026) | Not disclosed | Browse-and-ask; no product-specific ranking, alerts or regulation Q&A |
| **Mintel** (GNPD, Leap, Spark) | Syndicated research | CPG marketing, innovation, R&D | New-product launches (86 economies), consumer panels | Leap, Spark, GNPD Deep Research | Not disclosed | No ranking, alerts or regulation Q&A |
| **Statista** | Statistics portal | Analysts, consultants | 1.5M+ aggregated statistics | Research AI (cited); Connect API/MCP (Apr 2025) | Not on official site | No trade/tariff data; pull-only |
| **ITC Trade Map / MAcMap / Export Potential Map** | Free public tool | SMEs, trade-promotion bodies | Trade flows, tariffs/NTMs, **gravity-model export-potential ranking** | None embedded | Free | Generic (not manufacturer-specific), fixed method, not daily, no assistant |
| **S&P Global Panjiva** | Shipment data | Enterprise supply chain/compliance | Bills of lading, 21 countries | No dedicated GenAI | Not disclosed | No ranking or synthesis |
| **ImportGenius** | Shipment data | SMB–enterprise | US + 25 countries shipment records | AI HS-code enrichment; company profiler (2025) | Tiers, no public figures | No ranking; classification only |
| **Tridge** (Tridge Eye) | Agri-food data & sourcing (Korean) | Food/agri value chain; Lotte Mart named as customer | Prices, trade data, reports, marketplace | **Eye AI Chat (cited)**, **Eye Speaker (alerts)**, Eye Echo (forecast, beta) | Tiers, no public figures | Sourcing orientation; no confirmed outbound destination ranking; no regulation Q&A |
| **Spate / Trendalytics** | AI consumer trends | Brand marketing, R&D | Search/social trend forecasting | Ask Spate; TrendPulse AI (Mar 2026) | On request | Different domain (trends within a market) |
| **aT KATI + ChaTi** | Korean public service | K-food exporters (SMEs) | Export stats, reports, non-tariff barriers, buyer matching | **ChaTi: cited RAG over ~80k docs (Dec 2025)** → planned "K-Food export AI agent" | Free | Generic; no adjustable, robust, manufacturer-specific ranking; monitoring not confirmed |
| **KOTRA + "AI 수출비서"** | Korean public service | Exporters, all industries | Market news, country profiles | AI export assistant announced for 2026 (beta; *live functionality unverified*) | Free | Cross-industry; maturity unverified |
| **KITA K-stat / TradeNAVI** | Korean public service | Exporters | Trade stats, tariff/TBT/SPS lookup | None confirmed | Free | Lookup, not decision support |
| **Consultants** | Services | Enterprise strategy | Tailored studies | Varies | Project fee | Slow, costly, stale, not continuous |
| **In-house spreadsheets** | Status quo | Analysts | Manual Excel/PowerPoint | — | Analyst time | Manual, inconsistent, error-prone |

Pricing is shown only where publicly stated. Secondary estimates are excluded or labeled *unverified* in the workbook.

### 3.2 Capability matrix
● full · ◐ partial · ○ none

| | Trade data | Consumer data | Regulation info | **Ranked recs** | **Weights + robustness** | **Cited AI** | **Continuous alerts** | Korean |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Euromonitor | ◐ | ● | ○ | ○ | ○ | ● | ○ | ○ |
| Mintel | ○ | ● | ○ | ○ | ○ | ● | ○ | ○ |
| Statista | ○ | ◐ | ○ | ○ | ○ | ● | ○ | ○ |
| ITC EPM / MAcMap | ● | ○ | ◐ | ● | ◐ | ○ | ◐ | ○ |
| Panjiva | ● | ○ | ○ | ○ | ○ | ○ | ● | ○ |
| ImportGenius | ● | ○ | ◐ | ○ | ○ | ◐ | ● | ○ |
| Tridge | ● | ◐ | ○ | ◐ | ○ | ● | ● | ◐ |
| aT KATI + ChaTi | ● | ◐ | ● | ◐ | ○ | ● | ○ | ● |
| KOTRA AI 수출비서 | ◐ | ◐ | ◐ | ◐ | ○ | ◐ | ○ | ● |
| Consultants | ◐ | ● | ◐ | ● | ◐ | ○ | ○ | ● |
| **WellGTM (target)** | ● | ◐ | ● | ● | ● | ● | ● | ● |

### 3.3 Positioning map
```
                     Manufacturer-specific ↑
                                         │
          Consultants ●                  │        ★ WellGTM (target)
                                         │
 One-off / static ───────────────────────┼─────────────────────── Continuous / monitored
                                         │
   ITC EPM ●   Euromonitor ● Mintel ●    │   ● Tridge     ● Panjiva / ImportGenius
   KITA ●  Statista ●   aT ChaTi ●       │
   KOTRA AI 수출비서 ◌ (planned)          │
                                         ↓ Generic / market-wide
```

### 3.4 Competitive implications
1. **Differentiate on the combination,** not on any one feature: a manufacturer-specific ranking with adjustable weights and P(TOP3), corrected data, cited evidence, regulation Q&A and daily monitoring.
2. **Tridge is the most relevant private reference in Korea.** It has strong AI alerts and cited chat, food focus and a Lotte group relationship (Lotte Mart). Differentiate on **outbound market selection for a manufacturer's own products**, not on sourcing data depth.
3. **Treat aT ChaTi and KOTRA as data sources and potential partners**, not head-on competitors. Their free, generic Q&A will improve; WellGTM's value is company-specific depth, explicit trade-offs and monitoring. *Implication for the vision:* Segment 2 (export-support organisations) may prefer to **build** rather than buy, so partnership or white-label is likelier than licensing ([00 §4](00_product_vision.md#4-who-we-serve-b2b), [08 §2](08_value_proposition_canvas.md#2-canvas-segment-2-export-support-organisations-horizon-3)).
4. **Complement syndicated research** (Euromonitor, Mintel, Statista). Large clients already pay for these; WellGTM is the last-mile decision layer and can cite them where licensed.
5. **Borrow ITC's methodological transparency.** Publish our scoring method and corrections; this is a trust asset with both judges and buyers.

---

## 4. Target segments & demand signals
| Segment | Size / signal | Evidence | Priority |
|---|---|---|---|
| Large Korean food manufacturers with global targets | Lotte Wellfood overseas share ~28.6% vs target 35% by 2028; Orion ~66%, Samyang ~81% overseas | [02 §3–4](02_market_analysis.md#3-lotte-wellfood-profile-as-it-relates-to-export-market-selection) | Design partner (H1–H2) |
| Mid-size K-food exporters | K-food export growth; often no market-intelligence team (*assumption*) | [02 §2](02_market_analysis.md#2-market-context-k-food-exports) | H3 |
| Export-support organisations | aT and KOTRA are building their own AI tools | §3.1 | Partner (H3), not a primary buyer |
| Non-Korean food exporters | Method is origin-agnostic | [00 §8](00_product_vision.md#8-product-evolution-horizons) | Later |

**Market addressed by the product (category demand in the design partner's priority markets):** SAM ≈ US$32.9B of category imports, of which Korea supplies ≈1.0% ([02 §8](02_market_analysis.md#8-market-sizing-tam--sam--som)). This is the market *our clients* compete in, not WellGTM's software revenue pool. A bottom-up software market estimate needs interview data on willingness to pay (survey Q19 and interviews).

---

## 5. Client insights

### 5.1 Status
| Activity | Target | Done | Status |
|---|---:|---:|---|
| Client interviews (personas A–F + advisors) | 12 | 0 | Not started: guide ready (§6.2) |
| Microsoft Forms survey | 30+ responses | 0 | Not started: survey ready (§6.3) |
| Concept/usability tests of demo | 3–5 | 0 | After R1.0 |

### 5.2 Hypotheses and current evidence (desk research only)
| # | Hypothesis | Current evidence (secondary) | Confidence | How we'll validate |
|---|---|---|:-:|---|
| H1 | First-pass market studies take weeks, mostly data assembly | Fragmented sources across Comtrade, KATI, KOTRA, KITA (§3.1); our pipeline needed mirror, hub and volume corrections ([03](03_data_analysis.md)) | Medium | Survey Q6; interviews: time breakdown |
| H2 | Implicit weighting leads to challenged recommendations | The TOP3's third slot changes with weights ([03 §3](03_data_analysis.md#3-preliminary-screen-hypothesis-only)) | Medium | Q9; interview stories |
| H3 | Tariff/regulation changes are noticed late and cost money | Korean confectionery exports fell ~26% YoY in July 2025 as the US tariff deal took shape; Indonesia halal date changed Oct 2026 ([02](02_market_analysis.md)) | Medium–High | Q10; examples |
| H4 | Users trust AI insights if every number is sourced | Incumbents and public tools all market "cited" AI (T8, T9); ROI scepticism (T4) | Medium | Q18 top-2-box ≥ 60% |
| H5 | Robustness (P(TOP3)) is valued over a single list | No competitor offers it (§3.2) | Low | Q14 vs Q13; concept test |
| H6 | Monitoring creates value between studies | Tariff-tool adoption (T6); alerting in Tridge, Panjiva, ImportGenius | Medium | Q16; pilot willingness |
| H7 | Korean language is required for adoption | Public tools are Korean-first (§3.1) | Medium | Q19; interviews |
| H8 | Data security is the main blocker for internal data (H2) | General enterprise AI barrier | Low–Medium | Q19; IT interviews |
| H9 | Export-support organisations would use it for SME advisory | aT and KOTRA are building their own tools → may prefer build/partner | **Low (weakened)** | Interviews with aT/KOTRA desks |

---

## 6. Client research programme

### 6.1 Plan
| Step | Tool | Output | Owner |
|---|---|---|---|
| Recruit 8–12 interviewees across personas | `Interview_Plan` sheet | Schedule | PM |
| 45-minute semi-structured interviews | Guide §6.2; `Interview_Log` sheet | Notes, tagged pains (P1–P9) and hypotheses (H1–H9) | PM + 1 note-taker |
| Survey (≈7 min) | Microsoft Forms (Quick import of the .docx) → *Open in Excel* → paste into `Survey_Responses` | Auto-calculated `Survey_Analysis` | PM |
| Synthesis | `Insight_Synthesis` sheet (affinity mapping) | Updated personas v2, VPC fit, backlog changes | PM |
| Concept/usability test | R1.0 demo | Task success, quotes | PM + Eng |

**Ethics:** obtain consent; record only what's needed; no confidential company data in the 예선; report survey results in aggregate.

### 6.2 Interview guide (45 min)
**Screener:** involved in choosing, analysing or executing export-market decisions in a food/CPG company, or advising exporters.

| Block | Time | Questions |
|---|---|---|
| Intro & consent | 3 min | Purpose; recording consent; confidentiality |
| Role & context | 5 min | Your role? Which markets/categories? How is success measured for you? |
| Last decision story | 12 min | "Tell me about the last time your company decided to enter or prioritise an export market." Who was involved? What data did you use? How long did it take? What was hard? What happened afterwards? |
| Data & tools | 7 min | Which sources do you trust? Where do numbers conflict? How do you check regulations and tariffs? Which tools do you pay for? |
| Monitoring | 5 min | How do you learn about changes (tariffs, rules, demand)? Give a recent example where you learned too late. |
| AI & trust | 5 min | Have you used AI for this work? What would make you trust an AI's market recommendation? What would make you stop? |
| Concept reaction | 6 min | Show the TOP3 card with P(TOP3), reasons and sources (mock-up or demo). What's useful? What's missing? Who else would need to see it? |
| Wrap-up | 2 min | Anything we didn't ask? Who else should we talk to? |

**Probes:** "Why?", "Can you show me?", "What did that cost?", "What did you do instead?". Avoid leading questions about features.

### 6.3 Survey (Microsoft Forms)
- **File:** [`WellGTM_client_survey_for_MS_Forms.docx`](workbooks/WellGTM_client_survey_for_MS_Forms.docx), 21 questions in 5 sections (About you, Current process, Pain points, Feature value, Trust & adoption).
- **Set-up:**
  1. In Microsoft Forms, choose **Quick import** and upload the .docx.
  2. Check the detected question types: set Q7 and Q19 to *multiple answers*; Q8–Q18 to *Rating 1–5* or *Likert*; Q20 to *Text*.
  3. Add branching (Q21 = Yes → ask for an email).
- **Analysis:** *Responses → Open in Excel* → copy all rows into `Survey_Responses` (keep the header row). `Survey_Analysis` shows counts, % share, averages, top-2-box and within-section ranks. It works with both text ("4") and numeric (4) Likert answers. Formulas were verified with test data in a separate copy.
- **Question source:** [`analysis/pm_config.py`](../../analysis/pm_config.py) (`SURVEY`). Edit there and rebuild so the Forms file and Excel headers stay in sync.

---

## 7. Recommendations
1. **Positioning statement:** "The decision layer for export-market selection: manufacturer-specific, explainable, continuously monitored." Lead with the combination, not with AI.
2. **Message to Lotte:** WellGTM complements Euromonitor/Mintel subscriptions and the free aT/KOTRA tools by turning them into a defensible, monitored TOP3 for *Lotte's* categories and footprint.
3. **Proof first:** publish the methodology, evaluation results and measured time savings; include the ROI model.
4. **Run the research programme** in §6 before 본선; update personas, the VPC and the backlog with real evidence.
5. **Downgrade Segment 2** (export-support organisations) from customer to **partner/data source** until interviews say otherwise; update the vision accordingly.
6. **Don't claim export-voucher eligibility** unless KOSMES or the operating body confirms it.

---

## 8. Sources
**Market & AI trends**
- [B1] The Business Research Company, "Trade Compliance Software Global Market Report 2025," via GlobeNewswire/Yahoo Finance, 2026-01-14 — https://finance.yahoo.com/news/trade-compliance-software-global-research-145700811.html
- [B2] Grand View Research, "Business Intelligence Software Market Report, 2026–2033" — https://www.grandviewresearch.com/industry-analysis/business-intelligence-software-market
- [B3] Precedence Research, "Business Intelligence Software Market" — https://www.precedenceresearch.com/business-intelligence-software-market
- [B4] McKinsey & Company, "The State of AI," 2025-11-05 — https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai
- [B5] McKinsey & Company, "Fortune or fiction? The real value of a digital and AI transformation in CPG," Oct 2024 — https://www.mckinsey.com/industries/consumer-packaged-goods
- [B6] BCG, "Are You Generating Value from AI? The Widening Gap," Oct 2025 — https://www.bcg.com/publications/2025
- [B7] Deloitte, "State of AI in Retail and CPG" (date precision unverified) — https://www.deloitte.com/us/en/industries/consumer.html
- [B8] Thomson Reuters Institute, "2025 Tariffs Survey" — https://www.thomsonreuters.com/en/institute/reports/2025-tariffs-survey
- [B9] KPMG, "Tariff pressures reshape tech investment," Sept 2025 survey — https://kpmg.com/us/en/articles/2025
- [B10] The Budget Lab at Yale, "State of U.S. Tariffs: November 17, 2025" (re-verify before external use) — https://budgetlab.yale.edu/research/state-us-tariffs

**Competitors**
- [C1] Euromonitor, "Launches Passport AI," 2024-09-30; "Launches Next-Generation Passport," 2026-10-06 — https://www.euromonitor.com
- [C2] Statista, "Research AI" and "Statista's next big AI leap" — https://www.statista.com/press
- [C3] Mintel, "Mintel Leap," "Announcing Mintel Spark" (~Dec 2024), "GNPD" — https://www.mintel.com
- [C4] ITC, "Export Potential and Diversification Assessments: methodology," 2023-06-27 — https://exportpotential.intracen.org ; Market Access Map — https://www.macmap.org
- [C5] S&P Global, ChatIQ launch (Capital IQ Pro), 2024-11-12 — https://press.spglobal.com ; Panjiva — https://panjiva.com
- [C6] ImportGenius, AI HS-code enrichment and Genius Company Profiler (2025-04-10) — https://www.importgenius.com/press-releases
- [C7] Tridge, "What is Tridge Eye?" — https://www.tridge.com/about/tridge-eye ; TechCrunch, Series D, 2022-08-24 ; Korea Times, 2025-08-06
- [C8] Spate, "Spate AI" — https://help.spate.nyc ; Trendalytics, "TrendPulse AI" (Mar 2026) — https://help.trendalytics.co

**Korean public services**
- [K1] Money Today, "aT AI '채티', 과학기술혁신대상 금상 수상," 2026-10-20 — https://www.mt.co.kr/policy/2026/10/20/2026102009442184423
- [K2] Yonhap, "'AI 수출비서' 등 40개 이행 상황 점검," 2026-03-25 — https://www.yna.co.kr/view/AKR20260325066000003
- [K3] KITA K-stat — https://stat.kita.net
- [K4] 중소벤처기업부 공고 제2024-629호, "2025년도 수출지원기반활용사업 참여기업 1차 모집공고," 2024-12-30 — https://www.mss.go.kr

Full research notes are retained in the session workspace. K-food market sources are listed in [02](02_market_analysis.md#sources).
