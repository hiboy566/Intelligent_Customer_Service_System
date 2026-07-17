from __future__ import annotations

from fastapi.testclient import TestClient

from service.app import app
from service.model_runtime import ModelRuntime


def fake_load(runtime: ModelRuntime) -> None:
    runtime.device = "cuda:0"


def fake_generate(
    runtime: ModelRuntime,
    messages: list[dict[str, str]],
    **_: object,
) -> tuple[str, int, int]:
    assert messages[-1]["role"] == "user"
    return "请提供脱敏后的订单号，我会协助核查。", 20, 12


def test_health_and_chat_contract(monkeypatch) -> None:
    monkeypatch.setenv("SERVICE_API_KEY", "test-secret")
    monkeypatch.setattr(ModelRuntime, "load", fake_load)
    monkeypatch.setattr(ModelRuntime, "generate", fake_generate)

    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["quantization"] == "bnb-4bit-nf4-double-quant"

        unauthorized = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "查物流"}]},
        )
        assert unauthorized.status_code == 401

        response = client.post(
            "/v1/chat/completions",
            headers={"Authorization": "Bearer test-secret"},
            json={
                "messages": [{"role": "user", "content": "查物流"}],
                "temperature": 0,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["object"] == "chat.completion"
        assert body["choices"][0]["message"]["role"] == "assistant"
        assert body["usage"] == {
            "prompt_tokens": 20,
            "completion_tokens": 12,
            "total_tokens": 32,
        }
