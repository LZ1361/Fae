from __future__ import annotations

import json
import mimetypes
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mingyun_app.core.inference import build_evidence_profile
from mingyun_app.core.model_config import ensure_report_token_budget, normalize_model_config
from mingyun_app.core.prompts import build_reading_prompt
from mingyun_app.providers.anthropic import AnthropicProvider
from mingyun_app.providers.deepseek import DeepSeekProvider
from mingyun_app.providers.mock import MockProvider
from mingyun_app.providers.openai_chat import OpenAIChatProvider
from mingyun_app.providers.openai_responses import OpenAIResponsesProvider


def _runtime_app_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "mingyun_app"
    return Path(__file__).resolve().parent


APP_DIR = _runtime_app_dir()
STATIC_DIR = APP_DIR / "static"
REGISTRY_PATH = APP_DIR / "model_registry.json"
ENV_PATH = APP_DIR / ".env"


def load_model_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def create_reading_response(payload: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    model_config = ensure_report_token_budget(resolve_model_config(payload, registry))
    evidence_profile = build_evidence_profile(payload)
    messages = build_reading_prompt(
        {
            "evidence_profile": evidence_profile,
            "style": payload.get("style") or "balanced",
            "mysticism_level": payload.get("mysticism_level") or 50,
        }
    )
    provider = _provider_for(model_config)
    result = provider.generate_json(messages, model_config)
    return {
        "provider": result.provider,
        "model": result.model,
        "evidence_profile": evidence_profile,
        "reading": result.content,
        "usage": result.usage,
    }


def test_model_connection(payload: str | dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload, str):
        payload = {"model_id": payload}
    model_config = resolve_model_config(payload, registry)
    if model_config["provider"] == "mock":
        return {"ok": True, "provider": "mock", "message": "本地模拟模型可用。"}

    try:
        provider = _provider_for(model_config)
        result = provider.generate_json(
            [
                {"role": "system", "content": "你只输出合法 json。"},
                {
                    "role": "user",
                    "content": '{"task":"连接测试，请返回 {\\"ok\\": true, \\"message\\": \\"ready\\"} 这个 json"}',
                },
            ],
            {**model_config, "default_params": {"temperature": 0, "max_tokens": 120}},
        )
        return {
            "ok": True,
            "provider": result.provider,
            "model": result.model,
            "message": "连接测试成功。",
            "usage": result.usage,
        }
    except Exception as exc:
        return {"ok": False, "provider": model_config.get("provider", "unknown"), "message": str(exc)}


def resolve_model_config(payload: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    runtime_config = payload.get("model_config") or {}
    model_id = payload.get("model_id") or runtime_config.get("id") or "mock-local"
    try:
        base_config = _find_model(model_id, registry)
    except ValueError:
        base_config = {}

    model_config = _deep_merge(base_config, runtime_config)
    if not model_config:
        raise ValueError("Missing model_config")

    model_config.setdefault("id", model_id)
    model_config.setdefault("display_name", model_config.get("model_id") or model_id)
    model_config.setdefault("provider", "openai_compatible")
    model_config.setdefault("api_format", "openai_compatible")
    model_config.setdefault("api_key_ref", "")
    model_config.setdefault("default_params", {"temperature": 0.3, "max_tokens": 6000})
    model_config.setdefault("pricing", {"input_per_million": 0, "output_per_million": 0})

    api_key = payload.get("api_key") or runtime_config.get("api_key")
    if api_key:
        model_config["runtime_api_key"] = api_key
    model_config.pop("api_key", None)
    return normalize_model_config(model_config)


def _find_model(model_id: str, registry: dict[str, Any]) -> dict[str, Any]:
    for model in registry["models"]:
        if model["id"] == model_id:
            return dict(model)
    raise ValueError(f"Unknown model_id: {model_id}")


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        elif value not in (None, ""):
            merged[key] = value
    return merged


def _provider_for(model_config: dict[str, Any]):
    provider = model_config["provider"]
    api_format = model_config.get("api_format")
    if provider == "mock":
        return MockProvider()
    if provider == "deepseek":
        return DeepSeekProvider(ENV_PATH)
    if provider == "openai" and api_format == "openai_responses":
        return OpenAIResponsesProvider()
    if provider in {"openai", "openai_compatible", "custom"} or api_format in {
        "openai_chat",
        "openai_compatible",
    }:
        return OpenAIChatProvider()
    if provider == "anthropic" or api_format == "anthropic_messages":
        return AnthropicProvider()
    raise RuntimeError(f"Provider {provider} is not supported by the current adapter set.")


class MingyunHandler(BaseHTTPRequestHandler):
    server_version = "MingyunMVP/0.2"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/models":
            self._send_json(_public_registry(load_model_registry()))
            return
        if parsed.path in {"/", "/index.html"}:
            self._send_file(STATIC_DIR / "index.html")
            return
        candidate = (STATIC_DIR / unquote(parsed.path.lstrip("/"))).resolve()
        if STATIC_DIR in candidate.parents and candidate.exists() and candidate.is_file():
            self._send_file(candidate)
            return
        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = self._read_json()
            registry = load_model_registry()
            if parsed.path == "/api/readings/generate":
                self._send_json(create_reading_response(payload, registry))
                return
            if parsed.path == "/api/models/test":
                self._send_json(test_model_connection(payload, registry))
                return
            self._send_json({"error": "Not found"}, status=404)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=400)

    def log_message(self, format: str, *args: Any) -> None:
        sys.stdout.write("%s - %s\n" % (self.address_string(), format % args))

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8") if length else "{}"
        return json.loads(body)

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, path: Path) -> None:
        data = path.read_bytes()
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)


def _public_registry(registry: dict[str, Any]) -> dict[str, Any]:
    models = []
    for model in registry["models"]:
        public_model = dict(model)
        public_model.pop("api_key_ref", None)
        public_model.pop("runtime_api_key", None)
        models.append(public_model)
    return {"models": models}


def main() -> None:
    host = "127.0.0.1"
    port = 8787
    httpd = ThreadingHTTPServer((host, port), MingyunHandler)
    url = f"http://{host}:{port}/"
    print(f"命运 running at {url}")
    if os.environ.get("MINGYUN_NO_BROWSER") != "1":
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    httpd.serve_forever()


if __name__ == "__main__":
    main()
