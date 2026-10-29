# 01 — Problem Discovery

> **Challenge (롯데웰푸드 K-푸드 수출 유망국가 발굴):** Analyse each country's food-market growth, consumption trends and import/export status. Identify the **TOP3 promising export countries** and present the evidence behind each recommendation.
>
> **Stage:** 예선 (proposal + working demo). There is no Lotte field data yet. The 본선 stage will provide field data and expects a working AI-agent prototype.

---

## 1. Problem statement
Lotte Wellfood's overseas teams decide where to push Korean-made products (Pepero, Choco Pie, Xylitol, ice cream, etc.) using research that is:
1. **Slow and manual.** Trade statistics, macro data, consumer trends and import regulations sit in separate sources (UN Comtrade, 관세청, KOTRA, aT/KATI, embassy reports, regulator websites). Analysts assemble them by hand for each request.
2. **Snapshot-based.** A market study is out of date once delivered. Nobody is watching for a tariff change, a demand spike or a regulation update until the next study.
3. **Opaque.** Recommendations depend on implicit weighting (growth vs size vs risk) that is rarely stated, so different teams reach different conclusions from the same data.
4. **Easy to misread.** Our data analysis ([03](03_data_analysis.md)) shows how simple readings mislead:
   - Nominal growth hides flat volumes: Korea's category exports grew +7.7%/yr in value but ≈0% in volume.
   - Re-export hubs look like great markets: the Netherlands ranked #3 in a naïve screen.
   - Mirror statistics disagree by up to 3×.

**The problem to solve:** *How might we give Lotte Wellfood's global business teams a fast, transparent and always-current way to identify and justify the best export markets, so decisions are evidence-based and repeatable rather than one-off studies?*

---

## 2. Stakeholders & personas

| Persona | Role (assumed) | Goals | Pains | What they need from the product |
|---|---|---|---|---|
| **P1 — Min-ji, Global Market Strategy Manager** (primary) | 해외사업/글로벌전략 team, owns the annual market-prioritisation review | Defend a TOP3 to leadership; allocate the marketing and sales budget | Weeks of data gathering; assumptions questioned in review meetings; no single source of truth | Ranking with adjustable weights, robust evidence, exportable report with sources |
| **P2 — Jun-ho, Export Sales Manager** | Manages distributors in a region (e.g. SEA) | Find which country × category to push next quarter; react to changes fast | Learns about tariff or regulation changes late; can't quickly size a market | Country deep-dive, category view, alerts on his countries |
| **P3 — Executive / decision maker** (임원) | Approves market-entry investments | Clear recommendation + risk view in minutes | Long reports, inconsistent methods across teams | One-page TOP3 summary, confidence level, "what would change the answer" |
| **P4 — Regulatory / QA specialist** | Checks labeling, additives, halal, registration | Avoid shipment rejections and recalls | Rules scattered across regulators and languages | Cited regulation answers per country/category; change notifications |
| **P5 — Brand / marketing manager** (Pepero, ice cream) | Global brand plans | Where is the brand or category trending | Trend data is anecdotal (social posts, news) | Trend indicators, category-level growth |
| **Judges (예선/본선)** | Evaluate business impact, agent completeness, AI capability | See a credible, working, accurate system quickly | Limited time; may visit at any hour | Instant demo, simulation sandbox, visible evidence and evaluation metrics |

> ⚠️ The personas are **assumptions** based on typical FMCG global-business org structures. If possible, validate them with Lotte Wellfood staff before 본선 (see §6).

---

## 3. Current ("as-is") workflow (assumed)

| Step | Activity | Typical sources | Assumed effort | Pain |
|---|---|---|---|---|
| 1 | Define the question (which categories, which regions) | Internal | 1–2 days | Scope creep; criteria not written down |
| 2 | Macro and market data aggregation | World Bank, IMF, Euromonitor (paid), Comtrade, 관세청, KATI | ~15 business days | Different units, years and definitions; manual Excel |
| 3 | Regulatory and tariff review | KOTRA, embassies, FDA/GACC/BPOM/JAKIM sites, FTA texts | ~20 business days | Multilingual, scattered, changes often |
| 4 | Trend and consumer review | News, social media, aT surveys, Hallyu reports | Several days | Anecdotal, hard to quantify |
| 5 | Forecast and modeling | Excel trend lines | ~10 business days | Short series, no backtesting |
| 6 | Synthesis and deck | PowerPoint | Several days | Weighting implicit; hard to update |
| 7 | Monitoring after the decision | Ad hoc | Continuous | Nobody owns it; changes noticed late |

The baseline used in the PRD (Epic 3) is **15 + 20 + 10 = 45 business days** for steps 2, 3 and 5. It is an **assumption to validate**.

---

## 4. Jobs-to-be-done
1. *When I prepare the annual market-priority review, I want to rank candidate countries on transparent criteria, so I can defend the TOP3 and show it holds up under different assumptions.*
2. *When a leader asks "why not country X?", I want to compare X with our TOP3 side by side, with sources, so I can answer in the meeting rather than a week later.*
3. *When I consider launching a category (e.g. ice cream) in a new country, I want to know its import rules, tariffs and halal requirements, with citations, so I don't plan a launch that will be blocked at customs.*
4. *When something changes in my markets (demand spike, tariff, regulation, FX), I want to be told proactively, so I can react before competitors do.*
5. *When I need to share findings, I want a ready-made report with charts and sources, so I don't rebuild a deck each time.*

---

## 5. Product hypotheses (to test with the prototype)

| # | Hypothesis | How we'll test it | Success signal |
|---|---|---|---|
| H1 | A transparent, weight-adjustable score with uncertainty (P(TOP3)) is more persuasive than a single ranked list | Judge/user feedback; demo walkthrough | Users change weights and cite P(TOP3) in reasoning |
| H2 | A grounded agent (tools + verifier + citations) can answer market questions accurately | Golden-question eval set | ≥90% numeric faithfulness, ≥85% correct citations |
| H3 | Monitoring + alerts creates ongoing value beyond a one-off study | Simulation demo; alert precision on replayed history | Alerts judged relevant; low false-alarm rate |
| H4 | A full first-pass screening can run in minutes instead of weeks | Timed end-to-end run (`eval/time_savings.py`) | Median < 5 minutes |
| H5 | Category-specific views (e.g. ice cream) give different, actionable TOP3s | Data analysis + demo | Category TOP3s differ meaningfully and the reasons are explainable |

---

## 6. Open questions & assumptions to validate
| # | Question | Why it matters | How to resolve |
|---|---|---|---|
| Q1 | Who exactly is the primary user (global strategy vs export sales)? | Shapes default views and presets | Ask organisers/mentors; check the 본선 brief |
| Q2 | Does "export" include production at Lotte's overseas plants, or only shipments from Korea? | Changes how countries with local plants (IND, KAZ, PAK, RUS, MMR) are treated | Entry-mode lens supports both; confirm with the 본선 brief |
| Q3 | Which categories matter most (confectionery vs ice cream vs other foods)? | Lotte Wellfood also sells non-confectionery foods (ex-Lotte Foods) | Keep HS scope configurable; start with 4 HS codes |
| Q4 | Is the 45-day baseline realistic? | The business-impact claim depends on it | Short interview, or cite comparable industry studies; label as an assumption |
| Q5 | What field data will 본선 provide (internal sales, distributor data, price data)? | Schema must accept it | Keep a common schema and a `source` tag |
| Q6 | Are paid sources (Euromonitor, Nielsen) available in 본선? | Would improve the trend pillar | Design with adapters; public data by default |

---

## 7. What success looks like (for this challenge)
- **Business impact:** a defensible TOP3 with evidence a Lotte manager would accept, plus a believable path to daily use (monitoring, reports).
- **Agent completeness:** a deployed, stable, accurate prototype that judges can use at any time, including the simulation.
- **AI capability:** sensible use of LLMs for tool use and RAG, with proper data science behind them (volume vs value, mirror checks, backtesting, sensitivity) rather than using the LLM to replace them.
