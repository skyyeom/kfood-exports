# WellGTM — K-Food Export Market Intelligence

A dashboard and AI agent that ranks export markets for Lotte Wellfood's confectionery, bakery and ice cream (HS 1704/1806/1905/2105), explains every recommendation with cited evidence, and keeps the data current through scheduled, automated ingestion. Built for the Lotte AX Challenge 2026.

## Start here
| Document | What it covers |
|---|---|
| [PRD](docs/PRD.md) | Goals, metrics, scope, requirements |
| [Engineering plan](docs/engineering_plan.md) | Architecture, data sources, ingestion flow, API, dashboard pages |
| [Data dictionary](docs/data_dictionary.md) | Tables, keys, units, provenance |
| [Gap analysis & M1 plan](docs/gap_analysis_and_m1_plan.md) | What the earlier plan was missing and how it was fixed |
| [PM docs](docs/pm/README.md) | Vision, discovery, market and data analysis, stories, roadmap, risks |

## Repository
| Path | Contents |
|---|---|
| `pipeline/` | Automated ingestion: source adapters, validation, upserts with revision tracking, run log, scoring (M1, in progress) |
| `analysis/` | Exploratory analysis behind [03_data_analysis.md](docs/pm/03_data_analysis.md) |
| `docs/` | Product and engineering docs; `docs/archive/` holds superseded drafts |

## Run the pipeline locally
```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pipeline.run --source fx          # one source; or --all
.venv/bin/pytest -q
```
Without `DATABASE_URL`, data goes to `data/local.db` (SQLite) and raw responses to `data/raw/`.

## Turn on the automation (one-time setup)
1. Create a free Supabase project. In the SQL editor, run [`supabase/migrations/0001_init.sql`](supabase/migrations/0001_init.sql). It creates the tables, read-only RLS policies, the Realtime feed and the private `raw` bucket.
2. In GitHub → Settings → Secrets and variables → Actions, add:

| Secret | Value |
|---|---|
| `DATABASE_URL` | Supabase → Project Settings → Database → connection string (session pooler) |
| `SUPABASE_URL` | `https://<project>.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Project Settings → API → service_role key |
| `COMTRADE_API_KEY` | Optional. A free key from comtradeplus.un.org lifts the 500-row preview cap |
| `KCS_API_KEY` | Optional. A data.go.kr key for 관세청 monthly exports; without it that source is logged as skipped |

3. Run each workflow once from the Actions tab (**Ingest (daily / weekly / monthly)** → Run workflow). Every run appears in `ingest_runs` with a link back to its GitHub job.

| Workflow | Schedule (KST) | Sources |
|---|---|---|
| `ingest-daily.yml` | 02:00 daily | fx (regulation pages join in M4) |
| `ingest-weekly.yml` | 03:00 Tuesday | comtrade, wdi, tariffs, kcs_monthly |
| `ingest-monthly.yml` | 04:00 on the 6th | pinksheet |

Tariff policy changes go in [`pipeline/tariff_overrides.yaml`](pipeline/tariff_overrides.yaml); the next weekly run records the change as a revision.

## Status
M0 discovery is done. M1 (data foundation and automated ingestion) is in progress: the pipeline, scheduled workflows and database schema are built; connecting a Supabase project is the remaining setup step. See the [roadmap](docs/pm/05_roadmap.md).
