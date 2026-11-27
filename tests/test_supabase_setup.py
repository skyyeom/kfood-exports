from pipeline.supabase_setup import check_env

GOOD = {
    "SUPABASE_URL": "https://abcdefghijklmnop.supabase.co",
    "SUPABASE_SERVICE_ROLE_KEY": "service-key",
    "DATABASE_URL": "postgresql://postgres.abcdefghijklmnop:pw@aws-0-ap-northeast-2.pooler.supabase.com:5432/postgres",
}


def test_complete_pooler_settings_pass():
    assert check_env(GOOD) == []


def test_missing_settings_are_named():
    problems = check_env({"SUPABASE_URL": GOOD["SUPABASE_URL"]})

    assert any("DATABASE_URL" in p for p in problems) and any("SUPABASE_SERVICE_ROLE_KEY" in p for p in problems)


def test_direct_ipv6_database_host_is_rejected_because_github_actions_cannot_reach_it():
    direct = GOOD | {"DATABASE_URL": "postgresql://postgres:pw@db.abcdefghijklmnop.supabase.co:5432/postgres"}

    assert any("Session pooler" in p for p in check_env(direct))


def test_database_and_api_urls_must_belong_to_the_same_project():
    other = GOOD | {"SUPABASE_URL": "https://zzzzzzzzzzzzzzzz.supabase.co"}

    assert any("different projects" in p for p in check_env(other))


def test_placeholder_password_is_caught():
    placeholder = GOOD | {"DATABASE_URL": GOOD["DATABASE_URL"].replace(":pw@", ":[YOUR-PASSWORD]@")}

    assert any("password" in p for p in check_env(placeholder))
