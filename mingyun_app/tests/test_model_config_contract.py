import unittest

from mingyun_app.app import load_model_registry, resolve_model_config


class ModelConfigContractTests(unittest.TestCase):
    def test_remote_runtime_model_requires_base_url(self):
        registry = load_model_registry()

        with self.assertRaisesRegex(ValueError, "base_url"):
            resolve_model_config(
                {
                    "model_config": {
                        "id": "custom-missing-url",
                        "display_name": "Custom Missing URL",
                        "provider": "openai_compatible",
                        "api_format": "openai_compatible",
                        "model_id": "qwen3:8b",
                    }
                },
                registry,
            )

    def test_remote_runtime_model_requires_model_id(self):
        registry = load_model_registry()

        with self.assertRaisesRegex(ValueError, "model_id"):
            resolve_model_config(
                {
                    "model_config": {
                        "id": "custom-missing-model",
                        "display_name": "Custom Missing Model",
                        "provider": "openai_compatible",
                        "api_format": "openai_compatible",
                        "base_url": "http://localhost:11434/v1",
                    }
                },
                registry,
            )

    def test_provider_default_base_url_is_applied_when_safe(self):
        registry = load_model_registry()

        config = resolve_model_config(
            {
                "model_config": {
                    "id": "runtime-deepseek",
                    "provider": "deepseek",
                    "api_format": "openai_compatible",
                    "model_id": "deepseek-v4-pro",
                }
            },
            registry,
        )

        self.assertEqual(config["base_url"], "https://api.deepseek.com")

    def test_base_url_is_normalized_without_trailing_slash(self):
        registry = load_model_registry()

        config = resolve_model_config(
            {
                "model_config": {
                    "id": "runtime-deepseek",
                    "provider": "deepseek",
                    "api_format": "openai_compatible",
                    "base_url": "https://api.deepseek.com/",
                    "model_id": "deepseek-v4-pro",
                }
            },
            registry,
        )

        self.assertEqual(config["base_url"], "https://api.deepseek.com")

    def test_runtime_model_default_max_tokens_is_large_enough_for_reports(self):
        registry = load_model_registry()

        config = resolve_model_config(
            {
                "model_config": {
                    "id": "runtime-openai-compatible",
                    "provider": "openai_compatible",
                    "api_format": "openai_compatible",
                    "base_url": "http://localhost:11434/v1",
                    "model_id": "qwen3:8b",
                }
            },
            registry,
        )

        self.assertEqual(config["default_params"]["max_tokens"], 6000)


if __name__ == "__main__":
    unittest.main()
