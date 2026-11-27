"""Dashboard login: password hashing, sessions and throttling of failed attempts."""

import pytest

from pipeline.auth import LoginThrottle, Sessions, hash_password, verify_password


def test_correct_password_verifies_and_wrong_one_does_not():
    stored = hash_password("correct horse battery")

    assert verify_password("correct horse battery", stored)
    assert not verify_password("correct horse batterY", stored)


def test_hash_never_contains_the_password_and_differs_each_time():
    a, b = hash_password("s3cret-pass"), hash_password("s3cret-pass")

    assert "s3cret-pass" not in a and a != b and a.startswith("scrypt:")


def test_malformed_stored_hash_is_rejected_not_crashing():
    assert not verify_password("anything", "not-a-hash")


def test_a_session_is_valid_until_it_expires():
    clock = [1000.0]
    sessions = Sessions(ttl_seconds=60, clock=lambda: clock[0])
    token = sessions.create("lotte")

    assert sessions.user(token) == "lotte"
    clock[0] += 61
    assert sessions.user(token) is None


def test_ending_a_session_signs_out():
    sessions = Sessions()
    token = sessions.create("lotte")

    sessions.end(token)

    assert sessions.user(token) is None and sessions.user("made-up-token") is None


def test_repeated_failures_lock_the_address_for_a_while():
    clock = [0.0]
    throttle = LoginThrottle(max_failures=3, lock_seconds=60, clock=lambda: clock[0])
    for _ in range(3):
        throttle.failed("1.2.3.4")

    assert throttle.locked("1.2.3.4") and not throttle.locked("5.6.7.8")
    clock[0] += 61
    assert not throttle.locked("1.2.3.4")


def test_a_successful_login_clears_earlier_failures():
    throttle = LoginThrottle(max_failures=3)
    throttle.failed("1.2.3.4")
    throttle.failed("1.2.3.4")

    throttle.succeeded("1.2.3.4")
    throttle.failed("1.2.3.4")

    assert not throttle.locked("1.2.3.4")


@pytest.mark.parametrize("password", ["", "short"])
def test_too_short_passwords_are_refused(password):
    with pytest.raises(ValueError):
        hash_password(password)


def test_hash_survives_being_loaded_from_env_by_a_shell(tmp_path):
    # Regression: "scrypt$16384$8$1$..." was mangled by `set -a; . ./.env` ($1, $8 … expand), so every
    # sign-in failed with "Wrong username or password."
    import subprocess

    stored = hash_password("correct horse battery")
    env = tmp_path / ".env"
    env.write_text(f"DASHBOARD_PASSWORD_HASH={stored}\n")

    loaded = subprocess.run(["bash", "-c", f'set -a; . "{env}"; printf %s "$DASHBOARD_PASSWORD_HASH"'],
                            capture_output=True, text=True, check=True).stdout

    assert loaded == stored and verify_password("correct horse battery", loaded)


def test_hashes_in_the_earlier_dollar_format_still_verify():
    legacy = hash_password("correct horse battery").replace(":", "$")

    assert verify_password("correct horse battery", legacy)
