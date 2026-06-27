from __future__ import annotations

from typing import Any


REMOTE_PROVIDERS = {"deepseek", "openai", "anthropic", "openai_compatible", "custom"}
RESERVED_REQUEST_KEYS = {
    "model",
    "messages",
    "stream",
    "response_format",
}

RESERVED_RESPONSES_KEYS = RESERVED_REQUEST_KEYS | {
    "input",
    "text",
    "max_output_tokens",
}

PROVIDER_DEFAULTS: dict[str, dict[str, str]] = {
    "deepseek": {
        "api_format": "openai_compatible",
        "base_url": "https://api.deepseek.com",
        "api_key_ref": "DEEPSEEK_API_KEY",
    },
    "openai": {
        "api_format": "openai_responses",
        "base_url": "https://api.openai.com/v1",
        "api_key_ref": "OPENAI_API_KEY",
    },
    "anthropic": {
        "api_format": "anthropic_messages",
        "base_url": "https://api.anthropic.com",
        "api_key_ref": "ANTHROPIC_API_KEY",
    },
    "openai_compatible": {
        "api_format": "openai_compatible",
        "base_url": "",
        "api_key_ref": "CUSTOM_API_KEY",
    },
    "custom": {
        "api_format": "openai_compatible",
        "base_url": "",
        "api_key_ref": "CUSTOM_API_KEY",
    },
}


def normalize_base_url(value: Any) -> str:
    return str(value or "").strip().rstrip("/")


def sanitize_request_params(params: Any) -> dict[str, Any]:
    return sanitize_params(params, RESERVED_REQUEST_KEYS)


def sanitize_responses_params(params: Any) -> dict[str, Any]:
    return sanitize_params(params, RESERVED_RESPONSES_KEYS)


def sanitize_params(params: Any, reserved: set[str]) -> dict[str, Any]:
    if not isinstance(params, dict):
        return {}
    return {
        str(key): value
        for key, value in params.items()
        if str(key) not in reserved and value is not None
    }


def merged_request_params(model_config: dict[str, Any]) -> dict[str, Any]:
    params = sanitize_request_params(model_config.get("default_params"))
    params.update(sanitize_request_params(model_config.get("extra_body")))
    params.update(sanitize_request_params(model_config.get("param_overrides")))
    return params


def build_json_chat_body(
    messages: list[dict[str, str]],
    model_config: dict[str, Any],
    *,
    default_model: str,
    default_temperature: float,
    default_max_tokens: int,
) -> dict[str, Any]:
    params = merged_request_params(model_config)
    body = dict(params)
    body.setdefault("temperature", default_temperature)
    body.setdefault("max_tokens", default_max_tokens)
    body["model"] = model_config.get("model_id") or default_model
    body["messages"] = messages
    body["response_format"] = {"type": "json_object"}
    return body


def ensure_report_token_budget(model_config: dict[str, Any], minimum: int = 6000) -> dict[str, Any]:
    normalized = dict(model_config)
    params = dict(normalized.get("default_params") or {})
    raw_max_tokens = params.get("max_tokens")
    try:
        max_tokens = int(raw_max_tokens)
    except (TypeError, ValueError):
        max_tokens = 0
    params["max_tokens"] = max(max_tokens, minimum)
    normalized["default_params"] = params
    if isinstance(normalized.get("param_overrides"), dict):
        overrides = dict(normalized["param_overrides"])
        override_max = overrides.get("max_tokens")
        try:
            override_tokens = int(override_max)
        except (TypeError, ValueError):
            override_tokens = 0
        if override_max is not None:
            overrides["max_tokens"] = max(override_tokens, minimum)
        normalized["param_overrides"] = overrides
    return normalized


def normalize_model_config(model_config: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(model_config)
    provider = str(normalized.get("provider") or "openai_compatible").strip() or "openai_compatible"
    defaults = PROVIDER_DEFAULTS.get(provider, {})

    normalized["provider"] = provider
    normalized["api_format"] = normalized.get("api_format") or defaults.get("api_format", "openai_compatible")
    normalized["base_url"] = normalize_base_url(normalized.get("base_url") or defaults.get("base_url", ""))
    normalized["api_key_ref"] = normalized.get("api_key_ref") or defaults.get("api_key_ref", "")

    if provider == "mock":
        normalized["base_url"] = ""
        normalized["model_id"] = normalized.get("model_id") or normalized.get("id") or "mock-local"
        return normalized

    model_id = str(normalized.get("model_id") or "").strip()
    if provider in REMOTE_PROVIDERS and not model_id:
        raise ValueError("Remote model_config requires model_id")
    normalized["model_id"] = model_id

    if provider in REMOTE_PROVIDERS:
        base_url = normalized["base_url"]
        if not base_url:
            raise ValueError("Remote model_config requires base_url")
        if not (base_url.startswith("https://") or base_url.startswith("http://")):
            raise ValueError("Remote model_config base_url must start with http:// or https://")

    if not isinstance(normalized.get("default_params"), dict):
        normalized["default_params"] = {"temperature": 0.3, "max_tokens": 6000}
    if isinstance(normalized.get("extra_body"), dict) or isinstance(normalized.get("param_overrides"), dict):
        normalized["param_overrides"] = merged_request_params(normalized)
    return normalized
