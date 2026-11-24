# WellGTM: gap analysis, plan improvements, and the start of M1

> Status: approved 2026-11-24. Supersedes the architecture in the archived Master Plan and Infra docs. Related: [PRD](PRD.md) · [Decision & risk log](pm/07_decision_risk_log.md) · [Roadmap](pm/05_roadmap.md)

## Context
WellGTM is a dashboard plus AI agent that ranks about 30 countries as K-food export targets for Lotte Wellfood (HS 1704/1806/1905/2105) for the Lotte AX Challenge 2026. The PM docs are strong: the PRD, stories, and decision and risk logs, plus a real exploratory analysis in `analysis/` that found volume vs value effects, hub distortion, mirror gaps, and P(TOP3). The plan still has gaps in three areas: **data collection and ingestion**, **analysis method**, and the **dashboard spec**. No product code exists yet. M1 was due 13 Nov and M2 is due 27 Nov (today is 24 Nov), so we're behind. This document records the gaps, the improved plan, and the M1 work that starts now.

## Key gaps found

**A. Conflicting and missing docs**
- `WellGTM_Master_Plan.md` and `WellGTM_Infra_Architecture.md` are the "original draft" that D1 rejected. They contradict the PRD on several points: mock data; Render/EC2 vs HF Spaces; OpenAI embeddings vs local ones; Prophet 12-month forecasts on *annual* data; `CORS *`; 4 uvicorn workers in 4 GB; a Streamlit cache note.
- The PRD §8.3 refers to an "engineering plan" that doesn't exist. There is also no data dictionary, no schema DDL, no API contract and no `pipeline/` directory. The root `README.md` is empty.

**B. Data collection and ingestion**
- A "daily refresh" of annual Comtrade data is the wrong model. Comtrade *revises* its data, so we need change detection with revision diffs (old → new values recorded per run), not blind re-pulls.
- Several listed sources have no collector yet: tariffs (WITS), FX, the regulation corpus, the Trends snapshot, and Taiwan.
- The most valuable source is missing: **관세청 / KITA monthly Korea exports by HS10 × country** (data.go.kr API). Without it we can't do monthly monitoring, tariff-impact tracking (US-29), a 12-month forecast, or HS6/HS10 product fit (Pepero vs bread inside 1905).
- Also missing:
  - **World Bank Pink Sheet** monthly cocoa, sugar and dairy prices (needed for DR-9).
  - **Comtrade imports by supplier** (for supplier concentration and competitor-country share).
  - FTA status (KORUS, RCEP, K-ASEAN).
  - Demand proxies: Korean diaspora population, KOFICE Hallyu survey, Netflix Top-10 K-content.
- The ingestion design needs:
  - idempotent upsert keys;
  - data validation (pandera);
  - unit and coverage checks;
  - a per-source run log;
  - a stated policy for raw payloads: kept in object storage (Supabase Storage) per run, never committed to the repo.
- `collect.py` uses the keyless preview API (500-row cap). Add an optional free-key path with a 100k-row cap.

**C. Analysis method**
- `analyze.py:180` fills missing pillars with the median *silently*, which breaks DR-4. Imputed values must be flagged.
- The 5-year CAGR uses the 2020 COVID year as its base, so it depends heavily on that one year. Use a log-linear slope over 2019–25 and keep the endpoint CAGR as a cross-check.
- Min-max scaling is relative to the candidate set, so toggling hubs changes every other country's score. Document this, or use fixed reference bounds.
- Per-category scoring (FR-1.4) has never been run. Coverage and volume data per HS code still need checking.
- Planned pillar indicators that aren't defined yet:
  - Korea's import share (headroom);
  - Korean unit value vs the market average (premium fit);
  - supplier HHI;
  - applied tariff and FTA status;
  - distance or freight cost.
- Applied-tariff rule (US-32 says "highest valid rate"): change it to the lower of MFN and the FTA rate, plus any additional duties.
- Forecasting: with about 10 annual points, drop Prophet. Use naïve, drift, damped-ETS and log-linear models with a backtest. Use the monthly 관세청 series for anything at monthly granularity.
- **Ranking backtest** (new credibility test): score with 2015–19 data only and check whether the ranking predicts actual 2020–25 Korean export growth (Spearman ρ).
- Weights: add a short swing-weighting/AHP exercise in the interview programme so the presets are grounded in what users actually prioritise.

**D. Dashboard spec**
- The only layout is the Master Plan mock. We need a page and information-architecture spec:
  1. Overview (KPIs, TOP3)
  2. Screening (sliders, presets, P(TOP3), a country × pillar heatmap matrix instead of the "Won't" world map)
  3. Country profile
  4. Category explorer (value vs volume vs price)
  5. Compare
  6. **Data health / Ingestion** (source freshness, last run, row counts, validation failures, coverage matrix, mirror gaps, revision diffs). This is a new requirement; it isn't in the PRD yet.
  7. Alerts
  8. Report
- View state should live in the URL so views can be shared.
- **Architecture improvement:** rankings and P(TOP3) for the default presets are recomputed after each ingest and stored in Postgres. Custom slider weights are re-ranked in a Web Worker over the live pillar table. The dataset is tiny (30 × 4 × 11), so this meets the ≤500 ms target with no server round-trip. Python stays the reference implementation, and parity fixtures keep the TypeScript version in step.

## Recommended deployment stack: live, automated data, deployed from GitHub
No data is committed to the repo by hand or by bot. Scheduled jobs pull from the source APIs and write to a live database. The dashboard reads that database live and **shows the automation itself**: when each job ran, what it changed, and whether it passed checks.

| Layer | Stack | Runs on |
|---|---|---|
| Repo + CI/CD | Monorepo; `uv` + ruff + pytest; pnpm + vitest + Playwright | GitHub Actions |
| Scheduler + ingestion workers | Python 3.12, pandas, pandera; `pipeline.run --source X` | **GitHub Actions cron** with a separate schedule per source (below). Also `workflow_dispatch`, so a run can be started from the dashboard |
| Database (single source of truth) | **Supabase Postgres**: `trade_flows`, `country_indicators`, `tariffs`, `commodity_prices`, `fx_rates`, `reg_documents`, `ingest_runs`, `ingest_events`, `data_revisions`, `alerts`; Supabase Realtime | Supabase (free tier) |
| Backend API + agent | FastAPI (`/v1/rankings`, `/v1/countries/{iso}`, `/v1/pipeline/runs`, `POST /v1/pipeline/trigger`, `/v1/agent/*`) + LangGraph + Chroma, Docker | **Hugging Face Spaces**, auto-deployed from GitHub on push to `main`. Alternative: Render |
| Frontend | Vite + React + TypeScript, TanStack Query, ECharts, Tailwind, supabase-js (read-only, RLS) | **GitHub Pages** (only the app shell is static; all data is fetched live) |
| Email | Brevo SMTP, sent by the anomaly step after each run | GitHub Actions |

**Per-source schedules, so there is real change to show** (annual Comtrade data alone would almost never change):

| Source | Cadence | What a run detects |
|---|---|---|
| FX (Frankfurter) | Daily | New rates → FX-swing signal |
| Regulation pages (FDA, BPJPH, GACC…) | Daily | Content-hash change → new doc version, re-embedded into RAG, alert |
| Tariffs (WITS + override file) | Weekly | Rate changes and their effective dates |
| 관세청 monthly Korea exports (HS10 × country) | Weekly check | A new month published → trade spike/drop signals, forecast update |
| World Bank Pink Sheet (cocoa, sugar, dairy) | Monthly | A new month → commodity context |
| UN Comtrade, WDI | Weekly check | New reporter-years and **revisions** to earlier figures (diff recorded) |

After each ingest, the pipeline validates the new data, upserts it, recomputes rankings and P(TOP3), stores a ranking snapshot, runs anomaly detection, and sends alerts.

**The dashboard shows the automation on an "Automation & Data Health" page:**
- A live run feed via Supabase Realtime: queued → fetching → validating → upserted → re-ranked, with durations.
- A per-source freshness clock (last success, next scheduled run, status badge).
- What changed in each run: rows added, rows revised (old → new values), validation failures, any TOP3 change.
- A "Run now" button: the API calls GitHub's `workflow_dispatch`, rate-limited, and the run appears in the feed.
- A ranking-history chart showing how the TOP3 moved across runs.
- Every number on every page shows its source and "updated N hours ago".

**Resilience without static data:** the frontend reads rankings and profiles straight from Supabase (anon key, read-only RLS). The dashboard keeps working while the HF Space is asleep; only chat and report generation wait for it to wake up (US-30).

Things to watch:
- GitHub disables scheduled workflows in a public repo after 60 days with no repo activity. To keep them alive, a keepalive Action or the HF Space pings the GitHub API. Cron jobs can also start a few minutes late, which is fine for this data.
- Supabase free projects pause after 7 days with no activity. The daily jobs prevent that.
- Secrets (Supabase service key, LLM key, 관세청 key, Brevo, a fine-grained GitHub token for dispatch) go in GitHub Actions secrets and HF Space secrets. The browser only ever gets the read-only anon key.
- The CORS rule on the Space allows only the Pages origin.

Workflows to add: `ci.yml`, `ingest-daily.yml`, `ingest-weekly.yml`, `ingest-monthly.yml` (each calls `pipeline.run --source …` and accepts dispatch), `deploy-frontend.yml` (→ Pages), `deploy-api.yml` (→ HF Space).

## Deliverables

### 1. Docs
- **This document** (`docs/gap_analysis_and_m1_plan.md`) records the findings A–D above.
- **New `docs/engineering_plan.md`:** this fills the PRD's missing reference. It covers:
  - the repo layout (`pipeline/`, `scoring/`, `api/`, `frontend/`, `eval/`);
  - the live-database + scheduled-ingestion architecture, with client-side re-ranking for custom weights;
  - the source catalogue (source, endpoint, key needed, cadence, revision policy, licence/terms);
  - the ingestion flow: fetch → store raw payload → validate → normalise → upsert with revision diff → run and event log → re-rank;
  - storage: Supabase Postgres for all data, runs and rankings; Supabase Storage for raw payloads;
  - the API contract (`/v1/health`, `/v1/rankings`, `/v1/countries/{iso}`, `/v1/pipeline/runs`, `POST /v1/pipeline/trigger`, `/v1/agent/*`);
  - the dashboard page spec (the 8 pages above, the widgets on each, and the data contract each one needs);
  - the forecasting method.
- **New `docs/data_dictionary.md`:** the `country_indicators`, `trade_flows`, `tariffs`, `commodity_prices` and `ingest_runs` tables, with keys, units and provenance columns.
- **Updates to existing docs:**
  - PRD: §8.3 links the engineering plan; §11 gets the new sources; FR-3.1 is reworded as revision detection; the Data health page is added as FR-4.6.
  - Stories: new US-34 "Data health page" and US-35 "Ranking backtest"; US-32 gets the corrected tariff rule.
  - `03_data_analysis.md` §4: add the CAGR-base and silent-imputation limitations.
  - `07_decision_risk_log.md`: add D18 "client-side scoring", D19 "drop Prophet", D20 "Master Plan superseded".
  - `05_roadmap.md` and `pm_config.py` ROADMAP: re-baseline the M1/M2 dates.
- **Superseded docs:** move the Master Plan and Infra docs to `docs/archive/` with a "superseded by PRD" banner, and write a real root `README.md`.

### 2. M1 code: the `pipeline/` package (built test-first per `skills/tdd.md`)
The test seams are confirmed before any tests are written. The proposed seams are each source adapter's `fetch → DataFrame` output, the validation step, and the end-to-end "reproduce 03" check.
- `pipeline/sources/`:
  - `comtrade.py` and `wdi.py`: refactored from `analysis/collect.py` (reusing `comtrade()`, `CANDIDATES`, `WDI`), plus HS6 and by-supplier pulls;
  - `pinksheet.py`: commodity prices;
  - `fx.py`: Frankfurter;
  - `wits_tariffs.py`, plus `tariff_overrides.yaml` with effective dates;
  - `kcs_monthly.py`: data.go.kr 관세청. It needs a free API key; if no key is set it skips cleanly and logs that.
- `pipeline/schema.py`: pandera schemas for the common schema in FR-4.1, with provenance columns and an `imputed` flag.
- `pipeline/run.py --source X`:
  - each source runs in isolation, so one failure doesn't stop the others;
  - each run writes `ingest_runs` and step-by-step `ingest_events` rows to Supabase, so the dashboard can show progress live;
  - each run upserts on natural keys and records changed values in `data_revisions`;
  - each run then recomputes the rankings.
- `pipeline/db.py`: SQL migrations for the tables in the data dictionary (`supabase/migrations/`) and a small repository layer. Local development and tests use a Postgres container with the same migrations.
- `pipeline/indicators.py`: moves the indicator logic out of `analyze.py` (`cagr`, `norm`, the pillar build), adds the log-linear slope and the imputation flags, and leaves `analyze.py` as a thin caller.
- `.github/workflows/ingest-{daily,weekly,monthly}.yml` (cron + `workflow_dispatch`) and `ci.yml` (pytest + ruff).

## Verification
- `pytest` passes, including a fixture-based test showing that `pipeline` reproduces the `analysis/output/t7` and `t11` scores and P(TOP3) within ±1%. That is the M1 exit criterion.
- A live run of `python -m pipeline.run --source fx` against a test Postgres writes `ingest_runs` and `ingest_events` rows and upserts the data. Running it a second time adds no rows and no revisions, which shows the run is idempotent.
- Triggering `ingest-daily.yml` by `workflow_dispatch` on GitHub writes a run row to Supabase.
- Forcing one source to fail (a bad URL) still lets the other sources complete, and the failure is logged.
- Every link between the docs resolves (checked with a quick grep for the linked file paths).
