# 07 — Decision & Risk Log

## 1. Decision log
| ID | Decision | Alternatives considered | Rationale | Evidence |
|---|---|---|---|---|
| D1 | Use **real public data**, not mock data | Mock data (as in the original WellGTM draft) | 결과 정확성 is judged; mock data can't support "추천 근거" | [03](03_data_analysis.md) |
| D2 | Scope = HS **1704, 1806, 1905, 2105** | Confectionery codes only | Ice cream is Lotte's real growth category (+13.1%/yr volume) | [03 F1](03_data_analysis.md), [02 §3.3](02_market_analysis.md) |
| D3 | **Volume-based growth** by default | Nominal value | Cocoa price shock: chocolate value +21.7% vs volume −13.3% in 2025 | [03 F3](03_data_analysis.md) |
| D4 | **Exclude hubs** by default (HKG, SGP, NLD, ARE) | Keep all | A naïve screen ranks NLD #3 | [03 F6](03_data_analysis.md) |
| D5 | **Korea-reported exports** are the primary measure of K-momentum | Partner-reported imports | Mirror ratios range from 0.31 to 3.9 | [03 F4](03_data_analysis.md) |
| D6 | Show **P(TOP3)**, not just a ranked list | Single "answer" | The third slot depends on weights | [03 §3](03_data_analysis.md) |
| D7 | **Entry-mode lens** for local-production markets | Ignore | Lotte produces in IND, KAZ, RUS, PAK, MMR | [02 §3.2](02_market_analysis.md) |
| D8 | **Russia excluded by default** (sanctions/payment risk), toggleable | Include | Business risk; data stops in 2021 | [03 F5](03_data_analysis.md) |
| D9 | China is an **export-only** market, ranked normally but annotated | Exclude | Lotte is exiting manufacturing there, yet China is still a top-3 export destination | [02 §3.2](02_market_analysis.md) |
| D10 | Google Trends as a **static snapshot** only | Live pytrends | Rate limits (429/403) from shared IPs | Engineering plan |
| D11 | **Monitoring is "Should"**, after the core TOP3 | Must | The challenge scores TOP3 + evidence first | [PRD §7](../PRD.md) |
| D12 | **Tariff overrides** with effective dates | MFN/FTA only | The US 15% tariff overrides KORUS | [02 §6](02_market_analysis.md) |
| D13 | PDF via **browser print** | Server-side WeasyPrint | Free-tier container size and RAM | Engineering plan |
| D14 | **Simulation sandbox** for judges | Wait for the cron | Judges review at arbitrary times | Engineering plan |
| D15 | Indonesia halal date = **18 Oct 2028** (PP 40/2026) | Oct 2026 (older sources) | Regulation enacted 14 Oct 2026; older sources are stale | [02 §6](02_market_analysis.md) [R5] |
| D16 | Position as the **manufacturer-specific decision layer** (ranked + explainable + monitored + regulation Q&A), complementing syndicated research and public tools | Compete on AI Q&A | No competitor combines all four; aT ChaTi and Tridge already offer cited AI chat | [09 §3](09_market_research_report.md#3-competitor--alternative-analysis) |
| D17 | Treat export-support organisations as **partners/data sources** before buyers | Primary Horizon 3 segment | aT and KOTRA are building their own AI tools | [09 §3.4](09_market_research_report.md#34-competitive-implications) |

## 2. Assumptions register
| ID | Assumption | Confidence | Validation plan |
|---|---|---|---|
| A1 | The primary user is the global strategy manager (P1) | Medium | 본선 brief / mentor feedback |
| A2 | The manual baseline is ~45 business days | Low–Medium | Interview; label as an assumption |
| A3 | Public data is sufficient for a credible 예선 TOP3 | Medium–High | The data analysis shows it's feasible, with corrections |
| A4 | Free tiers (HF, Vercel, Supabase, Brevo, LLM) handle demo load | Medium | Load test before submission |
| A5 | Lotte's plant list (IND, KAZ, RUS, PAK, MMR, BEL) is current | Medium | Re-check DART subsidiaries list |
| A6 | Pepero ≈ HS 1905 | Medium | Check customs classification rulings |

## 3. Risk register
| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | TOP3 seen as arbitrary because it changes with weights | High | High | P(TOP3), presets, TOPSIS cross-check, explain in demo | PM |
| R2 | Data gaps (Taiwan, VNM/ARE/MNG 2024+, Russia) | Certain | Medium | Coverage badges; Korea-reported data; Taiwan source | Data |
| R3 | LLM hallucinated numbers or citations | Medium | High | Tools-only facts, verifier, evaluation set | AI |
| R4 | Free LLM rate limits during judging | Medium | High | Cache default report/answers; provider fallback; demo video | Eng |
| R5 | HF Space cold start makes the app look broken | High | High | Warm-up loader, cached TOP3, keep-warm via daily job | Eng |
| R6 | Comtrade preview limits or outages | Medium | Medium | Snapshot in repo; retries; per-source isolation | Data |
| R7 | Regulation corpus stale or incorrect | Medium | High | Dated sources, change-hash monitoring, "no evidence" fallback | AI |
| R8 | Alert fatigue | Medium | Medium | Sensitivity levels, dedup, daily cap, replay tests | PM |
| R9 | Scope creep from monitoring features | Medium | Medium | Scope-cut order in [05 §3](05_roadmap.md) | PM |
| R10 | Overstated business-impact claims | Medium | High | Baseline labeled as an assumption; measured time; SOM labeled illustrative | PM |
| R11 | Copyright/terms for KOTRA/aT reports | Low | Medium | Link and summarise; don't redistribute full text | PM |
| R12 | Free public AI tools (aT ChaTi, KOTRA AI 수출비서) are seen as "good enough" | Medium | High | Differentiate on company-specific ranking, P(TOP3), corrections, monitoring; use public data as inputs; explore partnership | PM |
| R13 | ROI scepticism among CPG buyers | High | Medium | ROI model + measured time savings + published evaluation | PM |
| R14 | Personas and pains not validated (no interviews yet) | Certain (now) | High | Run the [09 §6](09_market_research_report.md#6-client-research-programme) programme before 본선 | PM |
