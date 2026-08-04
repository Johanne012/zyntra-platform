from app.security import generate_api_key, hash_api_key


def test_generate_api_key_shape() -> None:
    raw, digest, prefix = generate_api_key()
    assert raw.startswith("zyn_")
    assert len(digest) == 64
    assert prefix.startswith("zyn_")
    assert hash_api_key(raw) == digest


def test_hash_is_stable() -> None:
    assert hash_api_key("abc") == hash_api_key("abc")
    assert hash_api_key("abc") != hash_api_key("abd")
