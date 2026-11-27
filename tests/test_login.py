"""The dashboard requires signing in: tested over real HTTP against the actual server."""

import http.client
import json
import threading
import urllib.parse

import pytest
from test_preview import seeded_store

from pipeline.auth import hash_password
from pipeline.db import Store
from pipeline.preview import main, make_server

USER, PASSWORD = "lotte-gtm", "correct horse battery"


@pytest.fixture(scope="module")
def db_url(tmp_path_factory):
    # a file, not :memory: — SQLite gives each thread its own empty in-memory database
    return f"sqlite:///{tmp_path_factory.mktemp('login')}/w.db"


SERVERS = {}


def server_store_engine(port):
    return SERVERS[port].RequestHandlerClass.store.engine


@pytest.fixture(scope="module")
def server(db_url):
    srv = make_server(seeded_store(db_url), port=0, username=USER, password_hash=hash_password(PASSWORD))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    SERVERS[srv.server_address[1]] = srv
    yield srv.server_address[1]
    srv.shutdown()


def request(port, method, path, body=None, cookie=None, form=False):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    headers = {"Cookie": cookie} if cookie else {}
    data = None
    if body is not None:
        data = urllib.parse.urlencode(body) if form else json.dumps(body)
        headers["Content-Type"] = "application/x-www-form-urlencoded" if form else "application/json"
    c.request(method, path, body=data, headers=headers)
    r = c.getresponse()
    return r.status, dict(r.getheaders()), r.read()


def sign_in(port, password=PASSWORD):
    status, headers, body = request(port, "POST", "/login", {"username": USER, "password": password})
    cookie = headers.get("Set-Cookie", "").split(";")[0]
    return status, headers, body, cookie


def test_pages_redirect_to_the_login_page_when_signed_out(server):
    status, headers, _ = request(server, "GET", "/")

    assert (status, headers["Location"]) == (303, "/login")


def test_api_calls_are_refused_when_signed_out(server):
    status, _, body = request(server, "GET", "/api/state")

    assert status == 401 and json.loads(body)["error"] == "not signed in"


def test_login_page_is_public_and_has_labelled_fields(server):
    status, _, body = request(server, "GET", "/login")

    html = body.decode()
    assert status == 200 and 'autocomplete="username"' in html and 'autocomplete="current-password"' in html
    assert '<label for="username"' in html and '<label for="password"' in html


def test_wrong_password_is_rejected_without_a_session(server):
    status, headers, body, _ = sign_in(server, password="wrong password!")

    assert status == 401 and "Set-Cookie" not in headers
    assert json.loads(body)["error"] == "Wrong username or password."


def test_signing_in_sets_a_protected_cookie_that_opens_the_dashboard(server):
    status, headers, body, cookie = sign_in(server)

    flags = headers["Set-Cookie"].lower()
    assert status == 200 and json.loads(body)["user"] == USER
    assert "httponly" in flags and "samesite=strict" in flags and "path=/" in flags
    assert request(server, "GET", "/api/state", cookie=cookie)[0] == 200
    assert request(server, "GET", "/", cookie=cookie)[0] == 200


def test_the_page_knows_who_is_signed_in(server):
    *_, cookie = sign_in(server)

    status, _, body = request(server, "GET", "/api/me", cookie=cookie)

    assert status == 200 and json.loads(body) == {"user": USER}


def test_signing_out_ends_the_session(server):
    *_, cookie = sign_in(server)

    request(server, "POST", "/logout", cookie=cookie)

    assert request(server, "GET", "/api/state", cookie=cookie)[0] == 401


def test_a_forged_cookie_is_refused(server):
    assert request(server, "GET", "/api/state", cookie="wellgtm_session=forged-token")[0] == 401


def test_repeated_wrong_passwords_lock_the_login_even_for_the_right_password(db_url):
    srv = make_server(Store(db_url), port=0, username=USER, password_hash=hash_password(PASSWORD))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    for _ in range(5):
        sign_in(port, password="wrong password!")

    status, _, body, _ = sign_in(port)

    srv.shutdown()
    assert status == 429 and "Too many" in json.loads(body)["error"]


def test_the_dashboard_will_not_start_without_a_configured_login(capsys):
    assert main(port=0, env={"DATABASE_URL": "sqlite://"}) == 2
    assert "python -m pipeline.auth set" in capsys.readouterr().out


def test_dashboard_data_is_cached_between_refreshes(server):
    # 2.3 s and ~700 KB per refresh against Supabase: repeated refreshes within the cache window must not
    # query the database again
    import sqlalchemy as sa

    *_, cookie = sign_in(server)
    request(server, "GET", "/api/state", cookie=cookie)
    queries = []
    store_engine = server_store_engine(server)
    listener = lambda *a, **k: queries.append(1)
    sa.event.listen(store_engine, "before_cursor_execute", listener)
    try:
        status, _, _ = request(server, "GET", "/api/state", cookie=cookie)
    finally:
        sa.event.remove(store_engine, "before_cursor_execute", listener)

    assert status == 200 and queries == []
