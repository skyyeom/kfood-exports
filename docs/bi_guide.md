# Connecting BI tools to WellGTM

WellGTM's data lives in Postgres (Supabase), so any BI tool can read it directly. The pipeline maintains flat, BI-friendly tables and views, refreshed automatically on every re-rank, so reports in Power BI, Looker Studio, Metabase or Tableau stay current with no manual exports.

## What to connect to

| Name | Kind | One row per | Use it for |
|---|---|---|---|
| `bi_rankings` | table | category × country | Current rank, score, the four pillar scores, P(TOP3), confidence and a one-line reason |
| `bi_forecast` | table | future year × country | Expected score, 80% range, expected rank, P(TOP3), forecast model |
| `bi_score_history` | table | year × country | Score and rank in each of the last 6 years |
| `bi_monthly_exports` | view | country × category × month | Korean exports (US$ FOB, kg) from 관세청; `month` is `YYYY-MM-01`; `WLD` = world total |
| `bi_annual_trade` | view | trade row | Comtrade annual imports and Korea-reported exports |
| `bi_pipeline_runs` | view | pipeline run | Data freshness and run health |

Category codes: `1704` sugar confectionery, `1806` chocolate, `1905` bakery & biscuits, `2105` ice cream, `all` = all four.

## Option A: connect live (recommended)

1. **Enable the read-only role** (one time, in the Supabase SQL editor). The migration already created `bi_reader` with SELECT on the tables and views above only. Give it a password:
   ```sql
   alter role bi_reader with login password '<a long random password>';
   ```
2. **Get the connection details:** Supabase → Project Settings → Database. Use the host, port `5432` (or the session pooler on `6543`), database `postgres`, user `bi_reader` and SSL **required**.
3. **Connect your tool:**
   - **Power BI Desktop:** Get data → PostgreSQL database. Enter the server as `host:port` and the database as `postgres`, choose **DirectQuery** for always-current data (or Import plus scheduled refresh), and sign in with `bi_reader`. Select the `bi_*` tables and views.
   - **Looker Studio:** Create → Data source → PostgreSQL. Enter the details above, tick "Enable SSL", then pick a `bi_*` table or view.
   - **Metabase:** Admin → Databases → Add → PostgreSQL, using the details above. Metabase can also email dashboards on a schedule.
   - **Tableau:** Connect → PostgreSQL, using the details above.
4. **Suggested first visuals:** a bar chart of `bi_rankings` (filter `category = 'all'`), a line chart of `bi_score_history` with `bi_forecast` (by `year`, legend `name`), and a line chart of `bi_monthly_exports` (by `month`, legend `category`, filter `iso3`).

`bi_reader` can only read: it has no insert, update or delete rights, and the dashboard's own tables are untouched.

## Option B: CSV files (Excel, or without a database)

- **From the dashboard:** Management → **Download BI data (CSV)** gives a zip with one CSV per table and view.
- **From the command line:**
  ```bash
  .venv/bin/python -m pipeline.bi export --out data/exports
  ```
  `data/exports/` is gitignored. CSVs are a snapshot; for live data use option A.
