"""One-command Supabase setup: check .env, apply the migration, verify, then load every source.

    set -a; . ./.env; set +a
    .venv/bin/python -m pipeline.supabase_setup            # add --skip-backfill to only migrate and verify

Never prints secrets: connection strings are shown without their password.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import sqlalchemy as sa

from pipeline.db import BI_TABLE_NAMES, BI_VIEWS, Store, metadata

MIGRATION = Path(__file__).resolve().parents[1] / "supabase/migrations/0001_init.sql"
REQUIRED = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "DATABASE_URL")


def _redacted(url: str) -> str:
    return re.sub(r":[^:@/]+@", ":****@", url)


def check_env(env) -> list[str]:
    """Problems with the Supabase settings, in plain language (empty = ready)."""
    problems = [f"{k} is not set in .env." for k in REQUIRED if not env.get(k)]
    if problems:
        return problems
    if "YOUR-PASSWORD" in env["DATABASE_URL"].upper():  # checked before parsing: the brackets confuse urlparse
        return ["DATABASE_URL has no real password; replace [YOUR-PASSWORD] with the database password."]
    api_ref = urlparse(env["SUPABASE_URL"]).hostname.split(".")[0]
    db = urlparse(env["DATABASE_URL"])
    if db.hostname and db.hostname.startswith("db.") and db.hostname.endswith(".supabase.co"):
        problems.append(
            "DATABASE_URL uses the direct host, which is IPv6-only and unreachable from GitHub Actions. "
            "Use the Session pooler string (Project Settings → Database → Connection string → "
            "Session pooler)."
        )
    user_ref = (db.username or "").removeprefix("postgres.")
    if user_ref and user_ref != "postgres" and user_ref != api_ref:
        problems.append(f"SUPABASE_URL ({api_ref}) and DATABASE_URL ({user_ref}) point to different projects.")
    if not db.password or "YOUR-PASSWORD" in (db.password or "").upper():
        problems.append("DATABASE_URL has no real password; replace [YOUR-PASSWORD] with the database password.")
    return problems


def apply_migration(store: Store) -> None:
    """Run the generated migration as one script (it is written to be re-runnable)."""
    raw = store.engine.raw_connection()
    try:
        with raw.cursor() as cur:
            cur.execute(MIGRATION.read_text())
        raw.commit()
    finally:
        raw.close()


def verify(store: Store) -> list[str]:
    """What is missing after the migration (empty = everything in place)."""
    insp = sa.inspect(store.engine)
    missing = [f"table {t}" for t in metadata.tables if not insp.has_table(t)]
    missing += [f"view {v}" for v in BI_VIEWS if v not in insp.get_view_names()]
    with store.engine.connect() as c:
        rls = {
            r[0]
            for r in c.execute(sa.text("select tablename from pg_tables where schemaname = 'public' and rowsecurity"))
        }
        missing += [f"row-level security on {t}" for t in metadata.tables if t not in rls]
        if not c.execute(sa.text("select 1 from storage.buckets where id = 'raw'")).first():
            missing.append("storage bucket raw")
        if not c.execute(sa.text("select 1 from pg_roles where rolname = 'bi_reader'")).first():
            missing.append("role bi_reader")
    return missing


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    env = os.environ
    if problems := check_env(env):
        print("Supabase settings need attention:\n- " + "\n- ".join(problems))
        return 2
    store = Store(env["DATABASE_URL"])
    print(f"Connecting to {_redacted(env['DATABASE_URL'])}")
    apply_migration(store)
    print("Migration applied.")
    if missing := verify(store):
        print("Missing after migration:\n- " + "\n- ".join(missing))
        return 1
    print(
        f"Verified: {len(metadata.tables)} tables with row-level security, {len(BI_VIEWS)} BI views, "
        f"raw bucket, bi_reader role ({', '.join(BI_TABLE_NAMES)} readable)."
    )
    if "--skip-backfill" in argv:
        return 0
    from pipeline.run import main as run

    print("Loading every source (full history; takes a few minutes)…")
    code = run(["--all"], env=env)
    run(["--rerank"], env=env)
    run(["--report"], env=env)
    return code


if __name__ == "__main__":
    sys.exit(main())
