"""Raw upstream responses: recorded during a fetch and archived per run (raw/{source}/{run_id}.zip)."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

SECRET_PARAMS = ("key", "token", "secret", "password")  # e.g. data.go.kr serviceKey, apikey, access_token


def _redact(params: dict | None) -> dict | None:
    if not params:
        return params
    return {k: "<redacted>" if any(s in k.lower() for s in SECRET_PARAMS) else v for k, v in params.items()}


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
                manifest.append({"file": name, "url": url, "params": _redact(params)})  # headers omitted: may hold keys
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


class SupabaseRawStore:
    """Supabase Storage bucket (default "raw"), written with the service-role key."""

    def __init__(self, url: str, service_key: str, bucket: str = "raw"):
        import requests

        self.base, self.bucket = url.rstrip("/"), bucket
        self.session = requests.Session()
        self.session.headers.update({"apikey": service_key, "x-upsert": "true", "Content-Type": "application/zip"})
        if not service_key.startswith("sb_secret_"):  # legacy service_role keys are JWTs and also go as Bearer
            self.session.headers["Authorization"] = f"Bearer {service_key}"

    def put(self, key: str, data: bytes) -> str:
        path = f"{self.bucket}/{key.removeprefix('raw/')}"
        r = self.session.post(f"{self.base}/storage/v1/object/{path}", data=data, timeout=60)
        if r.status_code >= 400:
            raise RuntimeError(f"Supabase Storage upload failed: HTTP {r.status_code}")
        return f"storage://{path}"
