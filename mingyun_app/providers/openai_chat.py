from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from mingyun_app.core.model_config import build_json_chat_body
from mingyun_app.providers.base import ProviderResult


class OpenAIChatProvider:
    def generate_json(self, messages: list[dict[str, str]], model_config: dict[str, Any]) -> ProviderResult:
        api_key_ref = model_config.get("api_key_ref", "OPENAI_API_KEY")
        api_key = model_config.get("runtime_api_key") or os.environ.get(api_key_ref)
        provider_name = model_config.get("provider", "openai")
        if not api_key:
            raise RuntimeError(f"Missing API key environment variable: {api_key_ref}")

        base_url = model_config.get("base_url", "https://api.openai.com/v1").rstrip("/")
        model_id = model_config.get("model_id", "gpt-5.4-mini")
        body = build_openai_chat_body(messages, {**model_config, "model_id": model_id})
        request = urllib.request.Request(
            f"{base_url}/chat/completions",
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{provider_name} API error {exc.code}: {error_body}") from exc

        raw_text = payload["choices"][0]["message"]["content"]
        parsed = json.loads(raw_text)
        usage = payload.get("usage", {})
        usage["estimated_cost_usd"] = _estimate_cost(model_config, usage)
        return ProviderResult(
            provider=provider_name,
            model=model_id,
            content=parsed,
            raw_text=raw_text,
            usage=usage,
        )


def build_openai_chat_body(messages: list[dict[str, str]], model_config: dict[str, Any]) -> dict[str, Any]:
    return build_json_chat_body(
        messages,
        model_config,
        default_model="gpt-5.4-mini",
        default_temperature=0.3,
        default_max_tokens=6000,
    )


def _estimate_cost(model_config: dict[str, Any], usage: dict[str, Any]) -> float:
    pricing = model_config.get("pricing", {})
    input_price = float(pricing.get("input_per_million", 0))
    output_price = float(pricing.get("output_per_million", 0))
    prompt_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
    return round((prompt_tokens / 1_000_000 * input_price) + (completion_tokens / 1_000_000 * output_price), 6)
