# 10 — User Persona Profiles

> **Status: proto-personas.** These profiles are based on desk research ([02](02_market_analysis.md)), typical FMCG global-business org structures, and the challenge brief. **No interviews have been conducted yet.**
> - Validate each persona with the [interview guide](09_market_research_report.md#6-client-research-programme) before 본선.
> - Names, quotes and day-in-the-life details are **illustrative**.
> - Fields marked 🔍 are the riskiest assumptions to test first.

---

## 1. The B2B buying committee at a glance

| Persona | Role in buying | Usage | Primary value driver | Priority |
|---|---|---|---|---|
| **A. Min-ji Park**, Global Market Strategy Manager | Champion; primary user | Weekly, deep | Defensible TOP3 in minutes | ★★★ Primary |
| **B. Jun-ho Lee**, Export Sales Manager (SEA/Americas) | User; influencer | 2–3× per week, focused | Early warning + country deep-dives | ★★ Secondary |
| **C. Seo-yeon Kim**, Sales Operations / Business Analyst | Power user; data steward | Daily | Less manual data wrangling | ★★ Secondary |
| **D. Hye-jin Choi**, Regulatory Affairs / QA Specialist | Influencer; can block a market | Weekly, on demand | Cited requirements + change alerts | ★★ Secondary |
| **E. Dong-hyun Jang**, Procurement & Raw-Materials Manager | Occasional user; influencer | Monthly + alerts | Input-cost and FX context for market decisions | ★ Tertiary |
| **F. Sang-woo Han**, Head of Global Business (임원) | Economic buyer; approver | Monthly + reports | Overseas-growth target with fewer bad bets | ★★★ Buyer |
| **G. IT / Information Security** | Gatekeeper | n/a | Security, SSO, data residency | Gate (Horizon 2) |

```
            Influence on purchase ↑
  F. Head of Global Business ●            (buyer / approver)
  D. Regulatory/QA ●        A. Strategy Mgr ● (champion)
  G. IT/Security ● (gate)    B. Export Sales ●
  E. Procurement ●           C. Sales Ops Analyst ●
                         → Frequency of use
```

---

## 2. Persona A — Min-ji Park, Global Market Strategy Manager (primary)

| | |
|---|---|
| **Org** | 글로벌전략 / 해외사업기획 team, Lotte Wellfood HQ (Seoul) |
| **Experience** | 8 years: 3 in consulting, 5 in corporate strategy |
| **Reports to** | Head of Global Business (Persona F) |
| **Measured on** 🔍 | Quality and timeliness of the annual market-priority review; overseas revenue-share progress (company target 35% by 2028); success of new-market launches |
| **Tools today** | Excel, PowerPoint, UN Comtrade/KATI downloads, KOTRA reports, consultant decks, internal sales BI |

**Goals**
1. Recommend a **TOP3** of export markets per category and defend it in front of executives.
2. Align strategy, sales and QA on one view of each market.
3. Spend her time on judgement, not data collection.

**Responsibilities:** annual and ad-hoc market studies; board/executive briefing decks; scoping new-market entry projects with sales and QA; working with consultants.

**A typical week (illustrative):** Mon: exec asks "why not Malaysia?" · Tue–Wed: pull trade data, reconcile years and units, chase a KOTRA report · Thu: rebuild charts · Fri: deck review where someone questions the weighting.

**Pains**
- 🔍 Data assembly takes weeks; numbers from different sources don't reconcile (we found mirror ratios of 0.31–3.9).
- The weighting is implicit, so leadership challenges the method rather than the market.
- Nominal growth inflated by price makes markets look better than they are.
- By the time the deck is approved, a tariff or rule has changed.

**Gains sought:** a review-ready answer with sources; a robustness view she can point to ("the US and China are TOP3 under 87% and 75% of weightings"); quick what-if analysis during the meeting.

**Quote (illustrative):** *"I don't need the tool to decide for me. I need it to show me, and my boss, why a market is in the TOP3 and what would change that."*

**How she'd use WellGTM**
1. Chooses the "Growth/entry" preset and the Ice cream category.
2. Checks P(TOP3) and the reason chips.
3. Asks the agent "필리핀 vs 말레이시아?"
4. Exports the PDF report for the exec meeting.

**Must-have features:** adjustable weights, presets, P(TOP3), reason packs, cited report, KO/EN.
**Success criteria:** report accepted without a "where did this number come from?" challenge; study time cut from weeks to hours.
**Adoption barriers:** distrust of AI numbers; "black box" fear; extra tool fatigue.
**Validation questions** 🔍: How many market studies a year? Who decides the weighting today? What made a past recommendation fail?

---

## 3. Persona B — Jun-ho Lee, Export Sales Manager (Southeast Asia & Americas)

| | |
|---|---|
| **Org** | 해외영업 team; manages distributors in 6–8 countries |
| **Experience** | 10 years in export sales; frequent travel |
| **Measured on** 🔍 | Export revenue and volume by country; distributor sell-in; new listings (e.g. Costco, convenience-store chains) |
| **Tools today** | Distributor reports, email/KakaoTalk, ERP sales data, occasional KOTRA news |

**Goals:** grow his countries' exports; decide which country × category to push next quarter; react quickly to market changes.

**Pains**
- 🔍 Learns about tariff or regulation changes from distributors, *after* orders are affected (e.g. the 15% US tariff from Aug 2025; Korean confectionery exports fell ~26% YoY in July 2025).
- Has no time for long reports; needs answers on a phone between meetings.
- Hard to size a new country quickly when a distributor pitches it.

**Gains sought:** short alerts on *his* markets; a one-screen country profile; quick comparisons for distributor negotiations.

**Quote (illustrative):** *"Tell me what changed in my markets this week, and whether I should care."*

**How he'd use WellGTM:** watchlist = PHL, VNM, USA, CAN × biscuits and ice cream. He gets an email brief when, for example, Philippine ice-cream imports from Korea jump. He clicks through to the country profile and asks the agent about labeling requirements before a new SKU listing.

**Must-have features:** watchlist, email briefs, mobile-friendly country profile, regulation Q&A.
**Success criteria:** hears about relevant changes from WellGTM first; fewer surprise delays at customs.
**Adoption barriers:** alert fatigue; poor mobile UX; data that doesn't match the internal sales numbers.

---

## 4. Persona C — Seo-yeon Kim, Sales Operations / Business Analyst (power user)

| | |
|---|---|
| **Org** | 영업기획 / Sales Operations; supports strategy and sales teams with data |
| **Experience** | 4 years; strong Excel/SQL, some Python |
| **Measured on** 🔍 | Report turnaround time, data accuracy, dashboard adoption |
| **Tools today** | Excel, internal BI, ERP extracts, Comtrade/KATI downloads, manual Power Query |

**Goals:** stop rebuilding the same datasets every quarter; give stakeholders self-service answers; keep data definitions consistent.

**Pains**
- 🔍 Repeated manual downloads, HS-code mapping and unit conversion.
- Gets the blame when two decks show different numbers.
- Every ad-hoc request ("exports to Mongolia by category since 2015?") takes half a day.

**Gains sought:** a trusted, versioned data layer with provenance; exports to Excel; clear data definitions; the ability to add internal data later.

**Quote (illustrative):** *"If every number has a source and a date, I can finally stop defending spreadsheets."*

**How she'd use WellGTM:**
- Checks the "data as of" dates and coverage badges.
- Exports tables to Excel.
- Reviews mirror-discrepancy warnings.
- Configures presets for her stakeholders.
- In Horizon 2, maps internal sales data into the common schema.

**Must-have features:** provenance on every value, coverage/imputation badges, CSV/Excel export, documented methodology, API access (later).
**Success criteria:** ad-hoc data requests answered in minutes; one source of truth.
**Adoption barriers:** can't export or audit the data; methodology not documented; numbers differ from internal BI without explanation.

---

## 5. Persona D — Hye-jin Choi, Regulatory Affairs / QA Specialist

| | |
|---|---|
| **Org** | 품질보증 / 해외인허가; checks labeling, ingredients/additives, certification (halal etc.) per market |
| **Experience** | 7 years; food science background |
| **Measured on** 🔍 | Zero shipment rejections or recalls; time to approve a new SKU for a new market |
| **Tools today** | Regulator websites, KOTRA/aT regulatory summaries, consultants, email alerts from industry bodies |

**Goals:** catch regulatory blockers before launch plans are made; keep up with rule changes across many countries and languages.

**Pains**
- 🔍 Rules are scattered, multilingual and change often. Example: Indonesia moved mandatory halal certification for imported food to 18 Oct 2028 (PP 40/2026, Oct 2026), and older sources still say 2026.
- Is consulted too late, after the strategy team has picked a market.
- Can't trust summaries without the original source.

**Gains sought:** cited answers that link to the primary document and its date; change alerts for monitored regulations; an early "regulatory burden" signal in the ranking.

**Quote (illustrative):** *"An answer without the regulation number and date is useless to me."*

**How she'd use WellGTM:** asks "인도네시아 ZERO 쿠키 할랄 인증 요건?" and gets an answer citing PP 40/2026, BPJPH and dates. She subscribes to regulation-change alerts for IDN, MYS and GCC.

**Must-have features:** regulation RAG with citations, a "no evidence found" fallback, document-change alerts, dated sources.
**Success criteria:** no blocked shipments from rules she didn't know about; involved earlier in market selection.
**Adoption barriers:** a single hallucinated rule destroys trust; the corpus is missing key countries.

---

## 6. Persona E — Dong-hyun Jang, Procurement & Raw-Materials Manager

| | |
|---|---|
| **Org** | 구매 / 원료조달; buys cocoa, sugar, dairy, oils, packaging |
| **Experience** | 12 years |
| **Measured on** 🔍 | Input cost vs budget; supply continuity; hedging effectiveness |
| **Tools today** | Commodity price feeds, supplier quotes, FX desk, ERP |

**Why he matters:** export choices change the input mix and cost exposure. Pushing chocolate-heavy products into price-sensitive markets during a cocoa shock squeezes margins: cocoa went from >US$12,000/t in late 2024 to ~US$6,200/t in Dec 2025, and Lotte's 2025 operating profit fell 30.3%.

**Goals:** a voice in market-expansion plans that affect demand for cocoa and dairy; early warning when export plans and input-cost risk collide.

**Pains**
- 🔍 Hears about export volume plans late, which hurts procurement forecasting.
- Commercial teams read nominal growth without seeing the commodity price effect.

**Gains sought:** visibility of category volume vs price trends (e.g. chocolate imports +21.7% value / −13.3% volume in 2025); FX and commodity context next to market recommendations.

**How he'd use WellGTM:** an occasional viewer of category value-vs-volume breakdowns; subscribes to FX-swing alerts; reviews the TOP3 report's "risks" section.

**Must-have features:** price-vs-volume breakdown, FX alerts, commodity context panel (*Could*).
**Adoption barriers:** low frequency of use; needs a narrow, relevant view.

---

## 7. Persona F — Sang-woo Han, Head of Global Business (economic buyer)

| | |
|---|---|
| **Org** | 글로벌사업본부장; owns overseas P&L and the 35%-overseas-by-2028 target |
| **Measured on** | Overseas revenue and share; profitability of overseas business; success of mega-brand (Pepero) expansion |
| **Tools today** | Executive reports, strategy decks, consultant studies |

**Goals:** hit the overseas-growth target with fewer bad bets; make faster, better-justified entry decisions; show the board a disciplined method.

**Pains**
- 🔍 Expensive consultant studies that are out of date quickly.
- Teams disagree; hard to compare recommendations made with different methods.
- Too concentrated in the USA, Japan and China (57% of Korea's category exports), and exposed to tariff shocks.

**Gains sought:** one-page TOP3 with a confidence level; "what would change the answer?"; evidence that the method is sound; ROI on the tool.

**Quote (illustrative):** *"Show me the three markets, how sure we are, and what it costs us if we're wrong."*

**Buying criteria** 🔍: credibility of the method, accuracy, time saved, security, cost, vendor viability.
**How he'd use WellGTM:** reads the TOP3 report; occasionally opens the dashboard during reviews.
**Success criteria:** faster decisions; an overseas share trending towards target; fewer reversed market decisions.

---

## 8. Persona G — IT / Information Security (gatekeeper, Horizon 2+)
- **Concerns:** data residency, SSO/SAML, access control, audit logs, handling of internal sales data, LLM data use (no training on customer data).
- **What we must provide:** a security overview, a data-flow diagram, tenant isolation, a configurable LLM provider (including on-prem/private endpoints), and audit logging.
- **Not relevant in 예선:** public data only, no confidential data.

---

## 9. Anti-personas (who we are *not* designing for)
- **Traders/brokers looking for buyer or supplier leads:** we don't provide matchmaking.
- **Consumers or researchers wanting general K-culture statistics:** out of scope.
- **Regulatory lawyers needing authoritative legal opinions:** WellGTM provides cited guidance, not legal advice.

---

## 10. Persona × feature matrix
● core · ○ occasional · – not used

| Feature | A Strategy | B Sales | C Analyst | D Reg/QA | E Procurement | F Exec |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| Weights, presets, P(TOP3) | ● | ○ | ● | – | – | ○ |
| TOP3 cards & reason packs | ● | ● | ○ | ○ | ○ | ● |
| Category filter | ● | ● | ● | ○ | ● | ○ |
| Country profile + provenance | ● | ● | ● | ○ | ○ | – |
| Value vs volume / price effect | ● | ○ | ● | – | ● | ○ |
| Forecast with intervals | ● | ○ | ● | – | ○ | ○ |
| Agent Q&A (KO/EN) | ● | ● | ○ | ● | ○ | ○ |
| Regulation RAG with citations | ○ | ● | – | ● | – | – |
| TOP3 report / PDF | ● | ○ | ○ | – | – | ● |
| Watchlist + email briefs | ○ | ● | ○ | ● | ● | ○ |
| Excel/CSV export | ○ | – | ● | – | ○ | – |
| Simulation sandbox | Demo | Demo | – | – | – | Demo |

---

## 11. Validation plan for personas
| Step | Method | Output |
|---|---|---|
| 1 | 6–10 interviews across personas A–F (guide in [09 §6](09_market_research_report.md#6-client-research-programme)) | Validated or revised goals, pains and KPIs |
| 2 | Microsoft Forms survey ([survey file](workbooks/WellGTM_client_survey_for_MS_Forms.docx)) to a wider audience | Quantified pain severity and feature priority |
| 3 | Affinity mapping in the [research workbook](workbooks/WellGTM_market_research.xlsx) (Interview_Log + Insight_Synthesis sheets) | Updated personas v2 |
| 4 | Usability test of the 예선 demo with 3–5 users | Task success rates; changes to the backlog |
