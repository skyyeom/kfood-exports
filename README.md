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

## Status
M0 discovery is done. M1 (data foundation and automated ingestion) is in progress. See the [roadmap](docs/pm/05_roadmap.md).
