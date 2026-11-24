import pytest
import requests

from pipeline.http import Http


class Upstream:
    """Stands in for the network: returns the given status codes in order."""

    def __init__(self, *statuses):
        self.statuses, self.calls = list(statuses), 0

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls += 1
        r = requests.Response()
        r.status_code, r._content, r.url = self.statuses.pop(0), b"ok", url
        return r


def client(upstream, attempts=3):
    http = Http(attempts=attempts, pause=0, sleep=lambda s: None)
    http.session = upstream
    return http


def test_retries_rate_limits_then_returns_the_body():
    assert client(Upstream(429, 503, 200)).get("https://api.example/x") == b"ok"


def test_gives_up_with_the_status_code_after_the_last_attempt():
    upstream = Upstream(503, 503, 503)

    with pytest.raises(RuntimeError, match="503"):
        client(upstream).get("https://api.example/x")
    assert upstream.calls == 3


def test_errors_never_include_query_strings_which_may_hold_api_keys():
    with pytest.raises(RuntimeError) as e:
        client(Upstream(403)).get("https://api.example/x", params={"serviceKey": "SECRET"})
    assert "SECRET" not in str(e.value) and "403" in str(e.value)
