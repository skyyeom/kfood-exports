"""Raw upstream responses: recorded during a fetch and archived per run (raw/{source}/{run_id}.zip)."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path


class RecordingHttp:
    """Wraps an HTTP client and keeps every response body, so a run's raw inputs can be archived."""

    def __init__(self, http):
        self.http, self.responses = http, []

    def get(self, url: str, params: dict | None = None, headers: dict | None = None) -> bytes:
        body = self.http.get(url, params=params, headers=headers)
        self.responses.append((url, params, body))
        return body

    def archive(self) -> bytes:
        buf, manifest = io.BytesIO(), []
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for i, (url, params, body) in enumerate(self.responses):
                name = f"{i:04d}.bin"
                z.writestr(name, body)
                manifest.append({"file": name, "url": url, "params": params})  # headers omitted: may hold keys
            z.writestr("manifest.json", json.dumps(manifest, indent=1, default=str))
        return buf.getvalue()


class LocalRawStore:
    def __init__(self, root: Path | str):
        self.root = Path(root)

    def put(self, key: str, data: bytes) -> str:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return str(path)
