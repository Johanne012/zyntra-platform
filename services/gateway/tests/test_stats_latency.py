from app.stats import StatsCollector


def test_latency_percentiles() -> None:
    c = StatsCollector()
    for ms in [10, 20, 30, 40, 50]:
        c.record_success("p", latency_ms=float(ms))
    snap = c.snapshot()
    lat = snap["providers"]["p"]["latency_ms"]
    assert lat["avg"] == 30.0
    assert lat["p50"] is not None
    assert lat["samples"] == 5
    assert snap["providers"]["p"]["success_rate_pct"] == 100.0
