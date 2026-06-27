import unittest

from mingyun_app.app import (
    create_reading_response,
    load_model_registry,
    resolve_model_config,
    test_model_connection,
)


class RuntimeModelConfigTests(unittest.TestCase):
    def test_custom_runtime_model_can_generate_with_mock_provider(self):
        registry = load_model_registry()
        response = create_reading_response(
            {
                "birth_date": "1998-05-06",
                "birth_time": "14:30",
                "birth_time_accuracy": "accurate",
                "birth_city": "上海",
                "calendar_type": "solar",
                "style": "balanced",
                "mysticism_level": 50,
                "model_config": {
                    "id": "custom-mock",
                    "display_name": "自定义模拟模型",
                    "provider": "mock",
                    "api_format": "local",
                    "model_id": "custom-mock-model",
                    "base_url": "",
                    "default_params": {"temperature": 0.2, "max_tokens": 1200},
                },
                "psychology_answers": {
                    "energy_social": 2,
                    "planning": 4,
                    "emotion_focus": 3,
                    "novelty": 4,
                },
            },
            registry,
        )

        self.assertEqual(response["provider"], "mock")
        self.assertEqual(response["model"], "custom-mock-model")

    def test_runtime_api_key_is_accepted_but_not_exposed_publicly(self):
        registry = load_model_registry()
        config = resolve_model_config(
            {
                "model_id": "openai-gpt-5-4-mini",
                "api_key": "secret-value",
                "model_config": {"model_id": "gpt-5.4-mini"},
            },
            registry,
        )

        self.assertEqual(config["runtime_api_key"], "secret-value")
        self.assertEqual(config["model_id"], "gpt-5.4-mini")

    def test_each_remote_model_has_base_url(self):
        registry = load_model_registry()
        remote_models = [
            item
            for item in registry["models"]
            if item["provider"] in {"deepseek", "openai", "anthropic", "openai_compatible"}
        ]

        self.assertTrue(remote_models)
        for model in remote_models:
            self.assertTrue(model["base_url"].startswith("https://"), model["id"])

    def test_deepseek_base_url_is_preserved_for_runtime_calls(self):
        registry = load_model_registry()
        config = resolve_model_config(
            {
                "model_id": "deepseek-v4-pro",
                "model_config": {
                    "base_url": "https://api.deepseek.com",
                    "model_id": "deepseek-v4-pro",
                },
            },
            registry,
        )

        self.assertEqual(config["base_url"], "https://api.deepseek.com")

    def test_openai_and_anthropic_are_real_provider_paths_not_placeholders(self):
        registry = load_model_registry()
        openai_result = test_model_connection(
            {
                "model_config": {
                    "id": "custom-openai",
                    "provider": "openai",
                    "api_format": "openai_chat",
                    "base_url": "https://api.openai.com/v1",
                    "model_id": "gpt-5.4-mini",
                    "api_key_ref": "OPENAI_API_KEY",
                }
            },
            registry,
        )
        anthropic_result = test_model_connection(
            {
                "model_config": {
                    "id": "custom-anthropic",
                    "provider": "anthropic",
                    "api_format": "anthropic_messages",
                    "base_url": "https://api.anthropic.com",
                    "model_id": "claude-opus-4-7",
                    "api_key_ref": "ANTHROPIC_API_KEY",
                }
            },
            registry,
        )

        self.assertEqual(openai_result["provider"], "openai")
        self.assertIn("API key", openai_result["message"])
        self.assertEqual(anthropic_result["provider"], "anthropic")
        self.assertIn("API key", anthropic_result["message"])


if __name__ == "__main__":
    unittest.main()
