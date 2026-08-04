from app.pricing import calc_cost_usd, get_price


def test_known_model_price() -> None:
    p = get_price("deepseek-chat")
    assert p.input_per_million == 0.14


def test_cost_zero_tokens() -> None:
    assert calc_cost_usd("deepseek-chat", 0, 0) == 0.0


def test_cost_positive() -> None:
    c = calc_cost_usd("deepseek-chat", 1_000_000, 1_000_000)
    # avoid float binary equality traps (0.14 + 0.28)
    assert abs(c - 0.42) < 1e-9
