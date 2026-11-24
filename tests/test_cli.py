from fakes import RecordedHttp

from pipeline.db import Store
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
