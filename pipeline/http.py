"""The real HTTP client used by sources: GET with retries on rate limits and transient server errors.

Error messages never include the query string, which can carry API keys (e.g. data.go.kr serviceKey).
"""

import time

import requests

RETRY_STATUS = {429, 500, 502, 503, 504}


class NotFound(RuntimeError):
    """HTTP 404. Some APIs (e.g. WITS) answer 404 when a query simply has no data."""


def _without_query(url: str) -> str:
    return url.split("?", 1)[0]


class Http:
    def __init__(self, attempts: int = 5, timeout: int = 90, pause: float = 1.0, sleep=time.sleep):
        self.attempts, self.timeout, self.pause, self.sleep = attempts, timeout, pause, sleep
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "WellGTM-pipeline/0.1 (+https://github.com/skyyeom/kfood-exports)"

    def get(self, url: str, params: dict | None = None, headers: dict | None = None) -> bytes:
        last = None
        for attempt in range(self.attempts):
            if attempt:
                self.sleep(5 * attempt)
            try:
                r = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
            except (requests.ConnectionError, requests.Timeout) as e:
                last = type(e).__name__
                continue
            if r.status_code in RETRY_STATUS:
                last = f"HTTP {r.status_code}"
                continue
            if r.status_code == 404:
                raise NotFound(f"HTTP 404 from {_without_query(url)}")
            if r.status_code >= 400:
                raise RuntimeError(f"HTTP {r.status_code} from {_without_query(url)}")
            self.sleep(self.pause)  # stay polite to keyless public APIs
            return r.content
        raise RuntimeError(f"Gave up after {self.attempts} attempts ({last}): {_without_query(url)}")
