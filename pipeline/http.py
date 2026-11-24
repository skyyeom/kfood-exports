"""The real HTTP client used by sources: GET with retries on rate limits and transient server errors."""

import time

import requests

RETRY_STATUS = {429, 500, 502, 503, 504}


class Http:
    def __init__(self, attempts: int = 5, timeout: int = 90, pause: float = 1.0):
        self.attempts, self.timeout, self.pause = attempts, timeout, pause
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "WellGTM-pipeline/0.1 (+https://github.com/skyyeom/kfood-exports)"

    def get(self, url: str, params: dict | None = None, headers: dict | None = None) -> bytes:
        for attempt in range(self.attempts):
            try:
                r = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
            except (requests.ConnectionError, requests.Timeout):
                if attempt == self.attempts - 1:
                    raise
            else:
                if r.status_code not in RETRY_STATUS:
                    r.raise_for_status()
                    time.sleep(self.pause)  # stay polite to keyless public APIs
                    return r.content
            time.sleep(5 * (attempt + 1))
        raise RuntimeError(f"Gave up after {self.attempts} attempts: {url}")
