"""Central password policy and Argon2id hashing through pwdlib."""

import re
import secrets

from pwdlib import PasswordHash

password_hasher = PasswordHash.recommended()
# Comparable work for unknown usernames, without a usable account or password.
_dummy_hash = password_hasher.hash("not-an-account-" + secrets.token_hex(32))


def normalize_username(username: str) -> str:
    value = username.strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{2,63}", value):
        raise ValueError("Use 3–64 letters, numbers, dots, underscores or hyphens.")
    return value


def hash_password(password: str) -> str:
    if not 12 <= len(password) <= 128:
        raise ValueError("Passwords must contain between 12 and 128 characters.")
    return password_hasher.hash(password)


def verify_and_upgrade(password: str, encoded: str | None) -> tuple[bool, str | None]:
    """Perform one verification and upgrade older hashes after a valid sign-in."""
    valid, updated = password_hasher.verify_and_update(password, encoded or _dummy_hash)
    return valid and encoded is not None, updated if encoded else None


def verify_password(password: str, encoded: str | None) -> bool:
    return verify_and_upgrade(password, encoded)[0]
