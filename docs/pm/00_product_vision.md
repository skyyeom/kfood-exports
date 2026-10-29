# 00 — Product Vision: WellGTM

> **One line:** WellGTM helps food manufacturers decide where to sell next, explain why, and notice when that answer changes.
>
> This document describes the long-term direction and the impact we want WellGTM to have on its B2B customers. The [PRD](../PRD.md) covers what we build now (예선 stage). This document explains why it is worth building and where it can go.

---

## 1. Vision statement
**Every export-market decision a food company makes should be based on current evidence, be explainable in one meeting, and be reviewed again when the market changes.**

## 2. Mission
Turn scattered trade statistics, consumer signals and import regulations into a **continuously updated, explainable market-prioritisation service** for food and consumer-goods manufacturers. Start with Lotte Wellfood and K-food exports.

## 3. The problem we exist to solve
Export expansion is one of the largest strategic bets a food manufacturer makes, yet the decision process is usually:

| Today | Consequence |
|---|---|
| **Fragmented.** Trade data, macro data, consumer trends and regulations sit in different places, languages and formats | Weeks of manual work per study. *Baseline assumption:* ~45 business days ([PRD §5.3](../PRD.md#53-workflow-time-savings-baseline-assumption-epic-3)) |
| **Snapshot-based.** A study is out of date on delivery | Tariff changes (e.g. the 15% US tariff since Aug 2025) and rule changes (e.g. Indonesia's halal deadline moved to Oct 2028) are noticed late |
| **Opaque.** Weighting between growth, size and risk is implicit | Teams reach different conclusions from the same data; recommendations are hard to defend |
| **Easy to misread.** Nominal figures and re-export hubs distort the picture | In our own analysis, Korea's category exports grew +7.7%/yr in value but ≈0% in volume, and a naïve screen ranked the Netherlands #3 ([03](03_data_analysis.md)) |

The cost is not only analyst time. The bigger cost is **misallocated market-entry budgets and missed timing**.

## 4. Who we serve (B2B)

### 4.1 Customer segments
| Horizon | Segment | Example | Why they buy |
|---|---|---|---|
| **Now: design partner** | Large Korean food manufacturer with global ambitions | **Lotte Wellfood**: overseas share ~28.6% (2025), target 35% by 2028; Pepero is the global mega brand | Faster, defensible market prioritisation; monitoring of existing markets |
| Next | Other Korean F&B exporters (large and mid-size) | Confectionery, ice cream, ramyeon, sauces, beverages | The same problem with fewer in-house analysts; mid-size firms have no market-intelligence team at all |
| Next | Export-support organisations | Public export agencies, trade associations, export voucher programmes | Consistent, evidence-based market advice at scale for many SMEs. ⚠️ aT (ChaTi) and KOTRA (AI 수출비서) are building their own AI tools, so treat this segment as **partner / data source first** ([09 §3.4](09_market_research_report.md#34-competitive-implications)) |
| Later | Global consumer-goods manufacturers and distributors in other origin countries | Asian or European snack and food makers expanding cross-border | The method doesn't depend on Korea; the data layer covers any origin–destination pair |

### 4.2 Buyers and users inside a customer
| Role | What they need | What success looks like for them |
|---|---|---|
| **Economic buyer:** Head of Global Business / Strategy | Hit overseas-growth targets with fewer bad bets | Better hit rate on market entries; faster review cycles |
| **Primary user:** global strategy manager | Defensible TOP3 per category, with evidence | Review-ready recommendation in minutes, not weeks |
| Export sales manager | Country deep-dives; early warning on their markets | Learns about changes from WellGTM, not from a distributor |
| Regulatory / QA | Cited regulatory requirements; change alerts | No shipments blocked by a rule they didn't know about |
| Executive | One-page answer with a confidence level | Can approve or challenge a recommendation in one meeting |

## 5. Value proposition
**For** global business teams at food manufacturers
**who** must decide which export markets to prioritise and defend that choice,
**WellGTM** is an AI market-intelligence service
**that** ranks markets on transparent, adjustable criteria, explains every recommendation with cited evidence, and alerts teams when the evidence changes.
**Unlike** consulting studies, syndicated market reports or raw trade databases,
**WellGTM** is **continuous** (refreshed daily), **explainable** (every number has a source and shows how robust the ranking is) and **actionable** (it produces the report and the watchlist, not just data).

## 6. Intended impact

### 6.1 Impact on the customer's business
| Impact area | From | To | How we'll know |
|---|---|---|---|
| **Decision speed** | Weeks per market study (assumed ~45 business days) | First-pass TOP3 with evidence in **minutes** | Measured end-to-end time (`eval/time_savings.py`) |
| **Decision quality** | Implicit weights; nominal data; hub distortions | Explicit weights, corrected data, robustness shown (P(TOP3)) | Share of market decisions supported by a WellGTM report; post-entry performance against the ranking |
| **Market visibility** | Periodic, manual checks | Daily monitoring with personalised alerts | Time from a market event (tariff, regulation, demand shift) to team awareness |
| **Regulatory risk** | Rules discovered late, by email or from distributors | Cited requirements up front, change alerts after | Fewer compliance surprises on new SKUs and markets |
| **Portfolio balance** | Exports concentrated: USA, Japan and China take 57% of Korea's category exports | Deliberate diversification with a measurable concentration view | Change in export concentration over time |
| **Organisational alignment** | Each team uses its own spreadsheet | One shared evidence base and method | Same data and method across strategy, sales and QA |

### 6.2 Impact on the user's day
- **Before:** gather data from many sources, reconcile units and years, build charts, write a deck, repeat next quarter.
- **After:** pick a strategy preset, adjust weights, ask follow-up questions in Korean or English, export the report. Alerts arrive only when something they watch changes.

### 6.3 What we will *not* claim
WellGTM speeds up and improves **first-pass screening and evidence assembly**. It does not replace local validation, distributor conversations or management judgement. All impact figures are either measured or clearly labeled as assumptions.

## 7. Long-term goals

| Goal | Description | Indicative outcome measures |
|---|---|---|
| **G1. Become the system of record for export-market decisions** | Every market-entry or expansion proposal at a customer starts from, and cites, a WellGTM ranking | Share of proposals with an attached WellGTM report; weekly active users in global business teams |
| **G2. Move from "where?" to "where, what, and how?"** | Recommend not only countries but the **product × market × entry mode** combination (export, distributor, local production) | Recommendations at product-line level (e.g. Pepero, ZERO, ice cream) with entry-mode rationale |
| **G3. Close the loop with real outcomes** | Feed actual sales, distributor and pricing data back into the models so recommendations learn from results | Forecast accuracy improvement after internal data is added; ranking back-tested against actual entry outcomes |
| **G4. Be the most trusted AI in the room** | Zero tolerance for ungrounded numbers; every claim traceable | Numeric faithfulness ≥ 95% and citation precision ≥ 90%, sustained in production |
| **G5. Scale beyond one company** | A multi-tenant SaaS used by multiple manufacturers and export-support organisations | Number of tenants; share of usage from non-design-partner customers |

## 8. Product evolution (horizons)
Horizons describe capability stages, not dates.

### Horizon 1: Prove it (current: Lotte AX Challenge)
- Public-data market ranking for 4 categories × ~30 countries, with data corrections (volume, hubs, mirror checks) and P(TOP3).
- Grounded AI agent: Q&A, dashboard control, regulation RAG, TOP3 report.
- Daily refresh, anomaly alerts, email briefs, and a simulation sandbox.
- **Exit signal:** Lotte stakeholders accept the TOP3 reasoning as defensible, and evaluation targets are met.

### Horizon 2: Embed it (single customer, production use)
- Connect **internal data**: sales by market and SKU, distributor sell-through, prices and margins.
- Product-level mapping (HS 6/10-digit ↔ brands such as Pepero, ZERO, World Cone).
- Entry-mode economics: compare export, distributor and local-production options, using existing plants (India, Kazakhstan) as regional hubs.
- Workflow integration: SSO, sharing reports internally, links to messenger/email, and an audit trail of decisions.
- **Exit signal:** WellGTM is used in the customer's annual market-priority review and quarterly business reviews.

### Horizon 3: Scale it (multi-customer SaaS)
- Multi-tenant platform with tenant-specific data, presets and strategic-fit factors.
- Additional categories (sauces, ramyeon, beverages, health foods) and origin countries.
- Premium data connectors (syndicated market data, retail scanner data, logistics rates) offered as add-ons.
- Benchmarking across customers, anonymised and opt-in only.
- **Exit signal:** paying customers beyond the design partner, with renewal driven by monitoring value.

## 9. Strategic pillars
1. **Evidence over opinion.** Provenance on every number. The AI explains and navigates; the data and models decide.
2. **Corrected by default.** Build domain knowledge into the defaults (volume vs value, re-export hubs, mirror discrepancies, current tariffs) so non-experts don't fall into known traps.
3. **Uncertainty is a feature.** Show how robust each recommendation is, so leaders can see where the decision is really a business trade-off.
4. **Continuous, not one-off.** The value grows as monitoring catches changes. Ongoing monitoring, not the first report, is what keeps customers.
5. **Bilingual and local-first.** Korean and English as equals, with local regulatory knowledge per market.
6. **Open data foundation, pluggable everything.** Public data first. LLMs, embeddings, data sources and delivery channels are swappable, which avoids lock-in and keeps costs low.

## 10. Positioning
| Alternative | Strength | Gap WellGTM fills |
|---|---|---|
| Management consulting studies | Deep, tailored | Slow, expensive, out of date on delivery, not interactive |
| Syndicated market research (e.g. Euromonitor, Mintel) | Rich category data | Static reports; no customer-specific ranking, weighting or alerts |
| Trade-data platforms (e.g. ITC Trade Map, Panjiva, ImportGenius, Tridge) | Raw or shipment-level trade data; Tridge adds cited AI chat and alerts | Users still have to interpret, correct and synthesise; no manufacturer-specific outbound ranking |
| Public export-information portals (e.g. aT KATI with the ChaTi AI assistant, KOTRA with its planned AI 수출비서) | Free, local knowledge; cited AI Q&A | Generic across exporters; no adjustable, robust ranking or confirmed monitoring. These are sources and partners, not just competitors |
| In-house spreadsheets | Full control | Manual, inconsistent, no monitoring |

**Our position:** the **decision layer** on top of these sources. It is opinionated about method, transparent about uncertainty, and continuous.

## 11. Business model hypothesis (Horizon 3)
- **Subscription per tenant**, tiered by number of markets/categories monitored and seats.
- **Add-ons:** premium data connectors, internal-data integration, custom regulatory corpora.
- **Public-sector licence** for export-support organisations serving many SMEs.
- **Cost discipline:** runs on low-cost infrastructure with pluggable models (the 예선 build runs entirely on free tiers).

> These are hypotheses to test after Horizon 2. They are not commitments.

## 12. What we will not do
- **Not** a trading marketplace or a sourcing platform. We inform decisions; we don't broker deals.
- **Not** a replacement for local market validation or regulatory counsel.
- **Not** a black box: we will not ship a recommendation we can't explain or source.
- **Not** dependent on any single LLM vendor or paid data source.
- **Not** sharing one customer's data with another, except opt-in anonymised benchmarks.

## 13. Key assumptions & risks to the vision
| Assumption / risk | Why it matters | How we'll test or mitigate |
|---|---|---|
| Customers value **explainable** rankings more than a single answer | Core differentiator | Design-partner feedback; demo reactions to P(TOP3) |
| Public data is good enough for a credible first product | Keeps cost and time-to-value low | Shown feasible in [03](03_data_analysis.md), with corrections and coverage badges |
| Monitoring creates recurring value | Drives retention in Horizon 3 | Alert usefulness ratings; usage between studies |
| Internal data can be integrated safely | Required for Horizon 2 | Common schema, tenant isolation, security review |
| AI trust can be maintained at scale | One bad number damages trust | Verifier, evaluation suite, continuous monitoring of faithfulness |
| The method transfers to other companies and categories | Required for Horizon 3 | Pilot a second category or customer before multi-tenancy |

## 14. How this vision guides today's decisions
| Today's choice ([PRD](../PRD.md)) | Vision link |
|---|---|
| Real public data with provenance | Pillar 1; G4 |
| Volume growth, hub exclusion, mirror checks by default | Pillar 2 |
| P(TOP3) and presets | Pillar 3 |
| Daily refresh, alerts, simulation | Pillar 4; G1 |
| KO/EN agent and regulation RAG | Pillar 5 |
| Pluggable LLMs, free-tier infrastructure | Pillar 6; §11 cost discipline |
| Common schema with a `source` tag | G3 (internal data) and Horizon 2 |
| Entry-mode lens | G2 (where, what, and how) |
