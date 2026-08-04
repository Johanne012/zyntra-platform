from app.balancer import ProviderBalancer


def test_priority_keeps_order() -> None:
    b = ProviderBalancer("priority")
    assert b.order(["a", "b", "c"]) == ["a", "b", "c"]


def test_round_robin_rotates() -> None:
    b = ProviderBalancer("round_robin")
    first = b.order(["a", "b", "c"])
    second = b.order(["a", "b", "c"])
    assert first != second or len(first) == 1
    assert set(first) == {"a", "b", "c"}


def test_random_permutation() -> None:
    b = ProviderBalancer("random")
    out = b.order(["a", "b", "c"])
    assert set(out) == {"a", "b", "c"}
