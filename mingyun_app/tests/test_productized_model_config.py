from pathlib import Path
import unittest

from mingyun_app.app import load_model_registry, resolve_model_config
from mingyun_app.core.model_config import ensure_report_token_budget
from mingyun_app.providers.openai_responses import build_openai_responses_body


STATIC_DIR = Path(__file__).resolve().parents[1] / "static"


class ProductizedModelConfigTests(unittest.TestCase):
    def test_registry_uses_official_provider_defaults(self):
        registry = load_model_registry()
        models = {model["id"]: model for model in registry["models"]}

        self.assertEqual(models["deepseek-v4-pro"]["base_url"], "https://api.deepseek.com")
        self.assertEqual(models["deepseek-v4-flash"]["model_id"], "deepseek-v4-flash")
        self.assertEqual(models["openai-gpt-5-5"]["api_format"], "openai_responses")
        self.assertEqual(models["openai-gpt-5-5"]["base_url"], "https://api.openai.com/v1")
        self.assertEqual(models["anthropic-claude-opus-4-8"]["model_id"], "claude-opus-4-8")
        self.assertNotIn("anthropic-claude-opus-4-7", models)

    def test_openai_responses_body_uses_responses_contract(self):
        messages = [
            {"role": "system", "content": "Only JSON."},
            {"role": "user", "content": "Return a report."},
        ]
        config = {
            "model_id": "gpt-5.5",
            "default_params": {"temperature": 0.2, "max_tokens": 6000},
            "param_overrides": {
                "top_p": 0.9,
                "model": "hijacked",
                "input": "hijacked",
                "text": {"format": {"type": "text"}},
            },
        }

        body = build_openai_responses_body(messages, config)

        self.assertEqual(body["model"], "gpt-5.5")
        self.assertIn("Only JSON.", body["input"])
        self.assertEqual(body["max_output_tokens"], 6000)
        self.assertEqual(body["text"]["format"], {"type": "json_object"})
        self.assertNotEqual(body["model"], "hijacked")

    def test_report_generation_enforces_minimum_output_budget(self):
        config = {
            "provider": "deepseek",
            "model_id": "deepseek-v4-pro",
            "base_url": "https://api.deepseek.com",
            "default_params": {"temperature": 0.2, "max_tokens": 120},
            "param_overrides": {"max_tokens": 120, "thinking_type": "disabled"},
        }

        raised = ensure_report_token_budget(config)

        self.assertEqual(raised["default_params"]["max_tokens"], 6000)
        self.assertEqual(raised["param_overrides"]["max_tokens"], 6000)
        self.assertEqual(raised["param_overrides"]["thinking_type"], "disabled")
        self.assertEqual(config["default_params"]["max_tokens"], 120)

    def test_main_page_links_to_separate_model_manager(self):
        html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")

        self.assertIn('href="/models.html"', html)
        self.assertNotIn('id="modelConfigForm"', html)
        self.assertNotIn('id="modelList"', html)

    def test_models_page_contains_model_manager_controls(self):
        html = (STATIC_DIR / "models.html").read_text(encoding="utf-8")
        script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="modelConfigForm"', html)
        self.assertIn('id="modelList"', html)
        self.assertIn('name="param_overrides"', html)
        self.assertIn('value="6000"', html)
        self.assertIn("return Math.min(16000, Math.max(6000, value));", script)
        self.assertIn("测试连接", html)

    def test_openai_responses_config_resolves_to_runtime(self):
        registry = load_model_registry()

        config = resolve_model_config(
            {"model_id": "openai-gpt-5-5"},
            registry,
        )

        self.assertEqual(config["api_format"], "openai_responses")
        self.assertEqual(config["model_id"], "gpt-5.5")


if __name__ == "__main__":
    unittest.main()
