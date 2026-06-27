from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from mingyun_app.core.model_config import sanitize_responses_params
from mingyun_app.providers.base import ProviderResult


class OpenAIResponsesProvider:
    def generate_json(self, messages: list[dict[str, str]], model_config: dict[str, Any]) -> ProviderResult:
        api_key_ref = model_config.get("api_key_ref", "OPENAI_API_KEY")
        api_key = model_config.get("runtime_api_key") or os.environ.get(api_key_ref)
        if not api_key:
            raise RuntimeError(f"Missing API key environment variable: {api_key_ref}")

        base_url = model_config.get("base_url", "https://api.openai.com/v1").rstrip("/")
        model_id = model_config.get("model_id", "gpt-5.5")
        body = build_openai_responses_body(messages, {**model_config, "model_id": model_id})
        request = urllib.request.Request(
            f"{base_url}/responses",
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
            raise RuntimeError(f"OpenAI Responses API error {exc.code}: {error_body}") from exc

        raw_text = extract_output_text(payload)
        parsed = json.loads(raw_text)
        usage = payload.get("usage", {})
        usage["estimated_cost_usd"] = _estimate_cost(model_config, usage)
        return ProviderResult(
            provider="openai",
            model=model_id,
            content=parsed,
            raw_text=raw_text,
            usage=usage,
        )


def build_openai_responses_body(messages: list[dict[str, str]], model_config: dict[str, Any]) -> dict[str, Any]:
    params = sanitize_responses_params(model_config.get("default_params"))
    params.update(sanitize_responses_params(model_config.get("extra_body")))
    params.update(sanitize_responses_params(model_config.get("param_overrides")))
    body = dict(params)
    body["model"] = model_config.get("model_id") or "gpt-5.5"
    body["input"] = "\n\n".join(
        f"{message.get('role', 'user').upper()}:\n{message.get('content', '')}"
        for message in messages
    )
    body["max_output_tokens"] = int(
        (model_config.get("default_params") or {}).get("max_tokens")
        or body.pop("max_tokens", 6000)
        or 6000
    )
    body.pop("max_tokens", None)
    body["text"] = {"format": {"type": "json_object"}}
    return body


def extract_output_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    parts: list[str] = []
    for output_item in payload.get("output", []) or []:
        for content_item in output_item.get("content", []) or []:
            if content_item.get("type") in {"output_text", "text"}:
                parts.append(content_item.get("text", ""))
    text = "\n".join(part for part in parts if part).strip()
    if not text:
        raise RuntimeError("OpenAI Responses API returned no output_text")
    return text


def _estimate_cost(model_config: dict[str, Any], usage: dict[str, Any]) -> float:
    pricing = model_config.get("pricing", {})
    input_price = float(pricing.get("input_per_million", 0))
    output_price = float(pricing.get("output_per_million", 0))
    input_tokens = int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
    return round((input_tokens / 1_000_000 * input_price) + (output_tokens / 1_000_000 * output_price), 6)
