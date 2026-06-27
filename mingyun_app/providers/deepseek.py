from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from mingyun_app.core.model_config import build_json_chat_body
from mingyun_app.providers.base import ProviderResult


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


class DeepSeekProvider:
    def __init__(self, env_path: Path | None = None) -> None:
        if env_path:
            load_env_file(env_path)

    def generate_json(self, messages: list[dict[str, str]], model_config: dict[str, Any]) -> ProviderResult:
        api_key_ref = model_config.get("api_key_ref", "DEEPSEEK_API_KEY")
        api_key = model_config.get("runtime_api_key") or os.environ.get(api_key_ref)
        if not api_key:
            raise RuntimeError(f"Missing API key environment variable: {api_key_ref}")

        base_url = model_config.get("base_url", "https://api.deepseek.com").rstrip("/")
        model_id = model_config.get("model_id", "deepseek-v4-pro")
        body = build_deepseek_chat_body(messages, {**model_config, "model_id": model_id})
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
            raise RuntimeError(f"DeepSeek API error {exc.code}: {error_body}") from exc

        raw_text = payload["choices"][0]["message"]["content"]
        parsed = parse_json_response(raw_text)
        usage = payload.get("usage", {})
        estimated_cost = _estimate_cost(model_config, usage)
        usage["estimated_cost_usd"] = estimated_cost
        return ProviderResult(
            provider="deepseek",
            model=model_id,
            content=parsed,
            raw_text=raw_text,
            usage=usage,
        )


def build_deepseek_chat_body(messages: list[dict[str, str]], model_config: dict[str, Any]) -> dict[str, Any]:
    body = build_json_chat_body(
        messages,
        model_config,
        default_model="deepseek-v4-pro",
        default_temperature=0.35,
        default_max_tokens=6000,
    )
    thinking_type = body.pop("thinking_type", None)
    if thinking_type in {"enabled", "disabled"}:
        body["thinking"] = {"type": thinking_type}
    return body


def _estimate_cost(model_config: dict[str, Any], usage: dict[str, Any]) -> float:
    pricing = model_config.get("pricing", {})
    input_price = float(pricing.get("input_per_million", 0))
    output_price = float(pricing.get("output_per_million", 0))
    prompt_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
    return round((prompt_tokens / 1_000_000 * input_price) + (completion_tokens / 1_000_000 * output_price), 6)


def parse_json_response(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        preview = text[:220].replace("\n", " ")
        raise RuntimeError(
            "模型返回的 JSON 不完整或格式无效；常见原因是 max_tokens 太小导致截断。"
            f" 请调高 max_tokens 后重试。预览: {preview}"
        ) from exc
