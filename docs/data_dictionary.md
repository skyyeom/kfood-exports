# WellGTM — Data Dictionary

The tables are defined in `pipeline/db.py`. The SQL in `supabase/migrations/` is generated from those definitions. Every data table carries the provenance columns `source`, `retrieved_at` (UTC ISO-8601, milliseconds) and `run_id`. **Key** marks the natural key used for upserts and revision detection.

- `retrieved_at` and `run_id` identify the run that **last changed** a row. Re-fetching an unchanged value leaves both alone, so "data as of" per source comes from the latest successful `ingest_runs.finished_at`.
- A payload must contain every key column and no duplicate keys, or the run fails without writing. Value columns absent from a payload are left unchanged.

## Data tables

### `trade_flows`
| Column | Type | Key | Notes |
|---|---|---|---|
| source | text | ✔ | `comtrade`, `kcs_monthly`, `lotte_field` (본선) |
| reporter_iso3 | text | ✔ | Reporting country (`KOR` for Korea-reported exports) |
| partner_iso3 | text | ✔ | `WLD` = world total |
| flow | text | ✔ | `M` import, `X` export |
| hs | text | ✔ | 4, 6 or 10 digits |
| freq | text | ✔ | `A` annual, `M` monthly |
| period | text | ✔ | `YYYY` or `YYYYMM` |
| value_usd | float | | Imports are CIF, exports FOB |
| net_kg | float | | Nullable; missing for some records (03 §4) |
| imputed | bool | | Always false for raw source rows |
| retrieved_at, run_id | | | Provenance |

### `country_indicators`
| Column | Type | Key | Notes |
|---|---|---|---|
| source | text | ✔ | `wdi`, `trends_snapshot`, … |
| iso3 | text | ✔ | |
| indicator | text | ✔ | e.g. `gdp_per_capita_usd`, `lpi_score` |
| year | int | ✔ | |
| value | float | | |
| unit | text | | e.g. `USD`, `%`, `persons`, `score` |
| source_code | text | | e.g. WDI code `NY.GDP.PCAP.CD` |
| imputed | bool | | |
| retrieved_at, run_id | | | |

### `tariffs`
| Column | Type | Key | Notes |
|---|---|---|---|
| source | text | ✔ | `wits`, `override` |
| importer_iso3 | text | ✔ | |
| hs | text | ✔ | |
| rate_type | text | ✔ | `mfn`, `pref`, `additional` |
| agreement | text | ✔ | e.g. `KORUS`, `RCEP`; empty string for MFN |
| effective_from | text | ✔ | ISO date |
| effective_to | text | | Nullable = still in force |
| rate_pct | float | | Ad-valorem percentage |
| source_url | text | | |
| retrieved_at, run_id | | | |

**Applied rate** = min(MFN, eligible preferential rate) + the sum of additional duties in force (for example, the US 15% reciprocal tariff on top of KORUS 0%).

WITS MFN rows are per HS6 line; overrides may be given at HS4, in which case they apply to every HS6 line that starts with that heading.

### `fx_rates`
| Column | Type | Key | Notes |
|---|---|---|---|
| source | text | ✔ | |
| date | text | ✔ | ISO date of the rate |
| base | text | ✔ | `USD` |
| quote | text | ✔ | ISO 4217 |
| rate | float | | Units of quote per 1 base |
| retrieved_at, run_id | | | |

### `commodity_prices`
| Column | Type | Key | Notes |
|---|---|---|---|
| source | text | ✔ | `pinksheet` |
| commodity | text | ✔ | `cocoa`, `sugar_world`, `wheat_us_hrw`, `palm_oil` |
| month | text | ✔ | `YYYY-MM` |
| price | float | | |
| unit | text | | e.g. `USD/kg`, `USD/mt` |
| retrieved_at, run_id | | | |

### `reg_documents` (M4)
`doc_id` (key), `country_iso3`, `title`, `url`, `content_hash`, `version`, `fetched_at`, `run_id`.

## Automation tables

### `ingest_runs`
| Column | Type | Notes |
|---|---|---|
| run_id | text (uuid) | Primary key |
| source | text | |
| trigger | text | `schedule`, `manual`, `ci`, `local` |
| status | text | `running`, `success`, `failed`, `skipped` |
| started_at, finished_at | text | UTC ISO |
| rows_fetched, rows_inserted, rows_updated, rows_unchanged, rows_invalid | int | |
| error | text | Nullable |
| ci_run_url | text | Link to the GitHub Actions run |

### `ingest_events`
`id` (autoincrement), `run_id`, `ts`, `step` (`start`, `fetch`, `validate`, `upsert`, `rerank`, `finish`), `status` (`ok`, `warning` (some rows rejected by validation), `error`, `skipped`), `message`, `metrics` (JSON).

### `data_revisions`
`id`, `run_id`, `table_name`, `row_key` (JSON of the natural key), `field`, `old_value`, `new_value`, `detected_at`. One row per changed field.

### `ranking_snapshots`
`id`, `run_id`, `computed_at`, `category` (`all` or an HS code), `variant` (`corrected`: volume growth, hubs excluded; `naive` reserved for the FR-1.6 toggle; `trend`: score history and forecast, see below), `preset` (`default` until M2 presets), `payload`.

`payload` is a JSON list ordered by rank, one object per country: `iso3`, `rank`, `score`, the four pillar values, `top3_probability` (±20% weights), `top3_prob_random_weights` (Dirichlet), `imputed_pillars` (pillars filled with the median), `missing_indicators` (indicators absent inside a pillar), `latest_year` (data year of the import figures), `hub` and `reasons`: a plain-language explanation built from the same data (`summary`; the two strongest pillars and the weakest, each with its rank and the facts behind it, with value, unit, period and source; `confidence` (`robust`, `depends on priorities` or `fragile`, from the two P(TOP3) values); and `caveats` such as mirror-data gaps, local production, hubs and missing data). Recompute after a scoring change with `python -m pipeline.run --rerank`.

The `trend` snapshot's payload is an object: `history` (score and rank per country for the latest 6 years, each year scored only with data known by then), `forecast` (per future year: expected `score`, 80% range `low`–`high`, expected `rank`, `p_top3` and the winning `model`), `holdout` (forecast of the latest year from the five before it vs what happened), `models` and `method`.

## Access (RLS)
- `anon`: `select` on every table above.
- `service_role` (pipeline): all writes.
- User tables (watchlists, alerts; M5): owner-only.
