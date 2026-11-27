"""Dashboard login: scrypt password hashes, in-memory sessions, and throttling of failed attempts.

    python -m pipeline.auth set      # asks for a username and password, writes them (hashed) to .env

.env holds DASHBOARD_USERNAME and DASHBOARD_PASSWORD_HASH; the plain password is never stored.
"""

from __future__ import annotations

import base64
import getpass
import hashlib
import hmac
import secrets
import sys
import threading
import time
from pathlib import Path

MIN_PASSWORD = 8
_N, _R, _P = 2**14, 8, 1  # scrypt cost parameters (≈16 MB, tens of ms per check)


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def hash_password(password: str) -> str:
    if len(password) < MIN_PASSWORD:
        raise ValueError(f"Use at least {MIN_PASSWORD} characters.")
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    return f"scrypt${_N}${_R}${_P}${_b64(salt)}${_b64(key)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt, key = stored.split("$")
        if scheme != "scrypt":
            return False
        derived = hashlib.scrypt(
            password.encode(), salt=_unb64(salt), n=int(n), r=int(r), p=int(p), dklen=len(_unb64(key))
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(derived, _unb64(key))


class Sessions:
    """Random session tokens held in memory; they end on sign-out, expiry or a server restart."""

    def __init__(self, ttl_seconds: int = 12 * 3600, clock=time.monotonic):
        self.ttl, self.clock = ttl_seconds, clock
        self._by_token: dict[str, tuple[str, float]] = {}
        self._lock = threading.Lock()

    def create(self, user: str) -> str:
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._by_token[token] = (user, self.clock() + self.ttl)
        return token

    def user(self, token: str | None) -> str | None:
        if not token:
            return None
        with self._lock:
            entry = self._by_token.get(token)
            if entry and entry[1] > self.clock():
                return entry[0]
            self._by_token.pop(token, None)
        return None

    def end(self, token: str | None) -> None:
        with self._lock:
            self._by_token.pop(token or "", None)


class LoginThrottle:
    """Lock an address out for a while after repeated failed sign-ins."""

    def __init__(self, max_failures: int = 5, lock_seconds: int = 60, clock=time.monotonic):
        self.max, self.lock_seconds, self.clock = max_failures, lock_seconds, clock
        self._failures: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _recent(self, address: str) -> list[float]:
        cutoff = self.clock() - self.lock_seconds
        recent = [t for t in self._failures.get(address, []) if t > cutoff]
        self._failures[address] = recent
        return recent

    def locked(self, address: str) -> bool:
        with self._lock:
            return len(self._recent(address)) >= self.max

    def failed(self, address: str) -> None:
        with self._lock:
            self._recent(address).append(self.clock())

    def succeeded(self, address: str) -> None:
        with self._lock:
            self._failures.pop(address, None)


def _write_env(path: Path, values: dict[str, str]) -> None:
    lines = path.read_text().splitlines() if path.exists() else []
    kept = [line for line in lines if line.split("=", 1)[0] not in values]
    path.write_text("\n".join(kept + [f"{k}={v}" for k, v in values.items()]) + "\n")
    path.chmod(0o600)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv != ["set"]:
        print("usage: python -m pipeline.auth set")
        return 2
    username = input("Dashboard username: ").strip()
    if not username:
        print("A username is required.")
        return 2
    password = getpass.getpass(f"Password (at least {MIN_PASSWORD} characters): ")
    if password != getpass.getpass("Repeat the password: "):
        print("The passwords do not match.")
        return 2
    try:
        hashed = hash_password(password)
    except ValueError as e:
        print(e)
        return 2
    env = Path(__file__).resolve().parents[1] / ".env"
    _write_env(env, {"DASHBOARD_USERNAME": username, "DASHBOARD_PASSWORD_HASH": hashed})
    print(f"Saved the login for {username!r} to {env} (password stored only as a hash). Restart the dashboard.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
