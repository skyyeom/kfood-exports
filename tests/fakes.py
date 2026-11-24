"""Test double for the external HTTP boundary: replays recorded upstream responses."""

from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


class RecordedHttp:
    def __init__(self, *routes: tuple[str, dict, str]):
        """routes: (url prefix, params that must match, fixture file name)."""
        self.routes = routes

    def get(self, url: str, params: dict | None = None, headers: dict | None = None) -> bytes:
        for prefix, match, fixture in self.routes:
            if url.startswith(prefix) and all(str((params or {}).get(k)) == str(v) for k, v in match.items()):
                return (FIXTURES / fixture).read_bytes()
        raise AssertionError(f"unexpected request: {url} {params}")
