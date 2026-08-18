import hashlib

from app.security import generate_api_key, hash_api_key


def test_generated_key_is_hashable_without_persisting_raw_secret() -> None:
    raw, digest, prefix = generate_api_key()
    assert raw.startswith("zyn_")
    assert prefix == raw[:12]
    assert digest == hashlib.sha256(raw.encode("utf-8")).hexdigest()
    assert hash_api_key(raw) == digest


def test_generated_keys_are_unique() -> None:
    first, _, _ = generate_api_key()
    second, _, _ = generate_api_key()
    assert first != second
