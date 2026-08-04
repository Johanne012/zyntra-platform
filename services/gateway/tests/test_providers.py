from app.config import Settings
from app.providers import build_providers, resolve_model


def test_build_providers_orders_default_first() -> None:
    s = Settings(gateway_default_provider="ollama", ollama_base_url="http://localhost:11434")
    providers = build_providers(s)
    assert providers[0].id == "ollama"


def test_resolve_model_default() -> None:
    s = Settings()
    providers = build_providers(s)
    ollama = next(p for p in providers if p.id == "ollama")
    assert resolve_model(ollama, None) == "llama3.2"
    assert resolve_model(ollama, "gpt-4o-mini") == "llama3.2"
