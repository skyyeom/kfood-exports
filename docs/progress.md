# WellGTM: progress and next steps

_Last updated 2026-11-24._

## Built
- **Pipeline** (`pipeline/`): scheduled ingestion of UN Comtrade, World Bank WDI, WITS tariffs + overrides, FX, the World Bank Pink Sheet and three 관세청 APIs; validation, revision tracking, run and step logs, raw-response archives, automatic re-ranking, score history and forecast, weekly reports.
- **GitHub workflows**: CI on SQLite and Postgres; ingest daily, weekly, monthly and 관세청 (17th); weekly report (Tuesday 05:00 KST).
- **Local dashboard** (`python -m pipeline.preview`, http://localhost:8765):
  - Overview: TOP3 for the current month, predicted TOP3, top-10 trend chart, all scored countries.
  - Country pages.
  - Trends.
  - Weekly reports.
  - Management: run feed, sources, Run all.

## Open requests
- **Tracker:** watch chosen countries and get alerts when they change. Proposal: pin countries from their page; a tracker view of rank, score and export changes since last week; alerts in the weekly report. This also covers the PRD watchlist (US-21).
- **BI tools:** the data is in Postgres (Supabase), so Power BI, Looker Studio, Metabase or Tableau can connect directly. Proposal: a read-only `bi_reader` role plus clean views (latest ranking, monthly exports, tariffs, run history). Power BI fits Lotte's Microsoft tooling.
- **Reference design:** the uxplanet article could not be fetched (HTTP 403). Paste its main points or screenshots to use it.

## Setup still needed
- Supabase project: run `supabase/migrations/0001_init.sql`, add the GitHub secrets listed in the README.
- FTA preferential rates for non-US markets in `pipeline/tariff_overrides.yaml` (needs cited sources); confirm the US 15% start date.
- Reissue the data.go.kr key (it appeared in chat) and keep it only in `.env` and the `KCS_API_KEY` secret.
