# WellGTM: progress and next steps

_Last updated 2026-11-27._

## Built
- **Pipeline** (`pipeline/`): scheduled ingestion of UN Comtrade, World Bank WDI, WITS tariffs + overrides, FX, the World Bank Pink Sheet and three 관세청 APIs; validation, revision tracking, run and step logs, raw-response archives, automatic re-ranking, score history and forecast, weekly reports.
- **GitHub workflows**: CI on SQLite and Postgres; ingest daily, weekly, monthly and 관세청 (17th); weekly report (Tuesday 05:00 KST).
- **Local dashboard** (`python -m pipeline.preview`, http://localhost:8765):
  - Overview: TOP3 for the current month, predicted TOP3, top-10 trend chart, all scored countries.
  - Country pages.
  - Trends.
  - Weekly reports.
  - Management: run feed, sources, Run all.

## Done since the pause (2026-11-25)
- **Tracker:**
  - Track any market from its country page.
  - The Tracker page shows rank and change since last week, monthly and 12-month exports, and the forecast TOP3 chance.
  - Alerts fire for a move of 2+ places, entering or leaving the TOP3, a ±30% monthly export swing and revised tariffs.
  - The sidebar shows an alert badge, and the weekly report has a section on tracked markets.
- **BI:**
  - Flat `bi_*` tables are refreshed on every re-rank, alongside views over the raw data.
  - A read-only `bi_reader` role is in the migration.
  - CSV export: `python -m pipeline.bi export`, or the Management page download.
  - The guide is in [bi_guide.md](bi_guide.md).

## Open
- **Reference design:** the uxplanet article could not be fetched (HTTP 403). Paste its main points or screenshots to use it.

## Supabase (done 2026-11-27)
- Project in ap-northeast-1. The migration is applied and verified.
- Full history is loaded: 8 sources, 0 failures. The data has been re-ranked and the first weekly report (2026-W48) is written.
- The local dashboard reads from Supabase when started with `.env` loaded.

## Setup still needed
- GitHub Actions secrets (needs a repo admin): `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `KCS_API_KEY`. Then merge PR #1 so the schedules run.
- FTA preferential rates for non-US markets in `pipeline/tariff_overrides.yaml` (needs cited sources); confirm the US 15% start date.
- Reissue the data.go.kr key (it appeared in chat) and keep it only in `.env` and the `KCS_API_KEY` secret.
