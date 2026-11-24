import os

import pytest
import sqlalchemy as sa
from fakes import RecordedHttp

from pipeline.db import Store, metadata
from pipeline.run import main

FX = ("https://open.er-api.com/v6/latest/USD", {}, "fx_open_er_api.json")
GITHUB = {
    "GITHUB_EVENT_NAME": "schedule",
    "GITHUB_SERVER_URL": "https://github.com",
    "GITHUB_REPOSITORY": "skyyeom/kfood-exports",
    "GITHUB_RUN_ID": "123",
}


def test_scheduled_github_run_is_logged_with_its_trigger_and_link(tmp_path):
    db = f"sqlite:///{tmp_path}/w.db"

    code = main(["--source", "fx"], env={"DATABASE_URL": db, **GITHUB}, http=RecordedHttp(FX))

    run = Store(db).runs().iloc[0]
    assert (code, run.trigger, run.ci_run_url) == (
        0,
        "schedule",
        "https://github.com/skyyeom/kfood-exports/actions/runs/123",
    )


def test_manual_dispatch_is_logged_as_manual(tmp_path):
    db = f"sqlite:///{tmp_path}/w.db"

    main(
        ["--source", "fx"],
        env={"DATABASE_URL": db, **GITHUB, "GITHUB_EVENT_NAME": "workflow_dispatch"},
        http=RecordedHttp(FX),
    )

    assert Store(db).runs().trigger.iloc[0] == "manual"


def test_exit_code_is_nonzero_when_any_source_fails_so_the_job_shows_red(tmp_path):
    code = main(
        ["--source", "fx", "--source", "wdi"], env={"DATABASE_URL": f"sqlite:///{tmp_path}/w.db"}, http=RecordedHttp(FX)
    )

    assert code == 1


def test_unknown_source_is_rejected():
    assert main(["--source", "nope"], env={}, http=RecordedHttp()) == 2


@pytest.mark.skipif("TEST_DATABASE_URL" not in os.environ, reason="needs a Postgres database")
def test_postgres_without_the_migration_fails_fast_instead_of_creating_tables_without_rls():
    url = os.environ["TEST_DATABASE_URL"]
    metadata.drop_all(Store(url).engine)

    code = main(["--source", "fx"], env={"DATABASE_URL": url}, http=RecordedHttp(FX))

    assert code == 3
    assert not sa.inspect(Store(url).engine).has_table("ingest_runs")


def test_rerank_recomputes_rankings_without_fetching_and_is_logged_as_a_run(tmp_path):
    from analysis_data import load_tables

    db = f"sqlite:///{tmp_path}/w.db"
    store = Store(db)
    store.create_all()
    trade, indicators = load_tables()
    seed = store.start_run("seed")
    store.upsert("trade_flows", trade, seed)
    store.upsert("country_indicators", indicators, seed)

    code = main(["--rerank"], env={"DATABASE_URL": db}, http=RecordedHttp())

    assert code == 0
    assert [c["iso3"] for c in store.latest_ranking()[:3]] == ["USA", "CHN", "PHL"]
    assert store.runs().set_index("source").loc["rerank", "status"] == "success"


def test_report_command_generates_and_stores_this_weeks_report(tmp_path):
    from analysis_data import load_tables

    db = f"sqlite:///{tmp_path}/w.db"
    store = Store(db)
    store.create_all()
    trade, indicators = load_tables()
    seed = store.start_run("seed")
    store.upsert("trade_flows", trade, seed)
    store.upsert("country_indicators", indicators, seed)
    main(["--rerank"], env={"DATABASE_URL": db}, http=RecordedHttp())

    code = main(["--report"], env={"DATABASE_URL": db}, http=RecordedHttp())

    assert code == 0
    [report] = store.list_reports()
    assert report["headline"].startswith("First report")
    assert store.runs().set_index("source").loc["report", "status"] == "success"
