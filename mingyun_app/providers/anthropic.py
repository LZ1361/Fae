from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

from mingyun_app.providers.base import ProviderResult


class AnthropicProvider:
    def generate_json(self, messages: list[dict[str, str]], model_config: dict[str, Any]) -> ProviderResult:
        api_key_ref = model_config.get("api_key_ref", "ANTHROPIC_API_KEY")
        api_key = model_config.get("runtime_api_key") or os.environ.get(api_key_ref)
        if not api_key:
            raise RuntimeError(f"Missing API key environment variable: {api_key_ref}")

        base_url = model_config.get("base_url", "https://api.anthropic.com").rstrip("/")
        model_id = model_config.get("model_id", "claude-opus-4-7")
        params = model_config.get("default_params", {})
        system = "\n".join(message["content"] for message in messages if message["role"] == "system")
        user_messages = [
            {"role": "user", "content": message["content"]}
            for message in messages
            if message["role"] != "system"
        ]
        body = {
            "model": model_id,
            "max_tokens": params.get("max_tokens", 6000),
            "system": system,
            "messages": user_messages,
        }
        if "temperature" in params:
            body["temperature"] = params["temperature"]
        request = urllib.request.Request(
            f"{base_url}/v1/messages",
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Anthropic API error {exc.code}: {error_body}") from exc

        raw_text = _content_text(payload)
        parsed = _parse_json_text(raw_text)
        usage = payload.get("usage", {})
        usage["estimated_cost_usd"] = _estimate_cost(model_config, usage)
        return ProviderResult(
            provider="anthropic",
            model=model_id,
            content=parsed,
            raw_text=raw_text,
            usage=usage,
        )


def _content_text(payload: dict[str, Any]) -> str:
    parts = []
    for item in payload.get("content", []):
        if item.get("type") == "text":
            parts.append(item.get("text", ""))
    return "\n".join(parts)


def _parse_json_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        cleaned = fence.group(1).strip()
    return json.loads(cleaned)


def _estimate_cost(model_config: dict[str, Any], usage: dict[str, Any]) -> float:
    pricing = model_config.get("pricing", {})
    input_price = float(pricing.get("input_per_million", 0))
    output_price = float(pricing.get("output_per_million", 0))
    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    return round((input_tokens / 1_000_000 * input_price) + (output_tokens / 1_000_000 * output_price), 6)
