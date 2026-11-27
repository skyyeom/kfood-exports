# Copilot instructions for WellGTM

WellGTM ranks export markets for Lotte Wellfood's confectionery, bakery and ice cream. `pipeline/` is a Python 3.12 package that ingests public trade data on GitHub Actions schedules, writes to Supabase Postgres, scores and forecasts markets, and serves a local dashboard (`pipeline/preview.py` + `preview.html`). Specs: `docs/PRD.md`, `docs/engineering_plan.md`, `docs/data_dictionary.md`.

## When reviewing, check that

**Data and provenance**
- Every stored row carries `source`, `retrieved_at` and `run_id`. Every number shown to users can be traced to a source and a year.
- Upserts go through `Store.upsert`, matched on the table's natural key. Changed values must be recorded in `data_revisions`, never overwritten silently.
- Missing data is flagged (`imputed`, `missing_indicators`), never silently filled.
- Growth uses volume, not value. Re-export hubs (HKG, SGP, NLD, ARE) are excluded from the corrected screen.

**Sources**
- Each adapter in `pipeline/sources/` returns a DataFrame in the data-dictionary shape.
- A source that can't run (e.g. a missing key) raises `SkipSource`. One failing source must never stop the others.
- APIs that report errors with HTTP 200 (관세청 `resultCode`, WDI `message`) are turned into exceptions.

**Secrets**
- No API keys, passwords or connection strings in code, tests, fixtures, logs, error messages or raw archives.
- Query-string keys (data.go.kr `serviceKey`) must be redacted. Error messages must not include query strings.

**Database**
- Tables are defined in `pipeline/db.py`. `supabase/migrations/0001_init.sql` is generated from it (`python -m pipeline.db`) and must not be edited by hand.
- SQL must run on both SQLite (tests) and Postgres (CI and Supabase).
- Row-level security: `anon` and `authenticated` may only read. `bi_reader` may only read the `bi_*` tables and views.

**Tests** (see `skills/tdd.md`, `skills/tests.md`, `skills/mocking.md`)
- New behaviour comes with a test written first, at a public interface. Fakes stand in only at system boundaries (HTTP, time); never mock internal code.
- Expected values come from an independent source: recorded real responses, the analysis outputs in `analysis/output/`, or hand-worked literals. They must never be recomputed the way the code computes them.
- A bug fix includes a regression test that failed before the fix.

**Style**
- Match the surrounding code: concise, sparse comments, module docstrings. ruff (config in `pyproject.toml`) must pass.
- Dashboard: never use colour alone (status = icon + label). Charts need a table view and keyboard access. Chart colours come from the palette validated with the dataviz skill.

Flag scope creep, untested behaviour and any change to `analysis/analyze.py`: it is the frozen reference the pipeline is tested against.
