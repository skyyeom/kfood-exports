"""render.yaml must stay in step with the code it deploys."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def service():
    [web] = yaml.safe_load((ROOT / "render.yaml").read_text())["services"]
    return web


def test_render_starts_the_dashboard_module_and_checks_the_public_health_route():
    web = service()
    module = web["startCommand"].split("-m ")[1].strip().replace(".", "/") + ".py"

    assert (ROOT / module).exists()
    assert web["healthCheckPath"] == "/healthz" and '"/healthz"' in (ROOT / "pipeline/preview.py").read_text()


def test_render_listens_publicly_behind_its_proxy():
    env = {e["key"]: e for e in service()["envVars"]}

    assert env["HOST"]["value"] == "0.0.0.0" and env["TRUST_PROXY"]["value"] == "1"


def test_every_secret_is_entered_in_render_not_committed():
    env = {e["key"]: e for e in service()["envVars"]}

    for key in (
        "DATABASE_URL",
        "DASHBOARD_USERNAME",
        "DASHBOARD_PASSWORD_HASH",
        "SUPABASE_SERVICE_ROLE_KEY",
        "KCS_API_KEY",
    ):
        assert env[key] == {"key": key, "sync": False}, key


def test_the_build_installs_the_postgres_driver():
    # Regression: "pip install ." left out psycopg (an optional extra) and the site crashed on startup
    assert ".[postgres]" in service()["buildCommand"]
