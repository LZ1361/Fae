import unittest

from mingyun_app.providers.deepseek import build_deepseek_chat_body
from mingyun_app.providers.openai_chat import build_openai_chat_body


class ProviderRequestParamTests(unittest.TestCase):
    def test_openai_compatible_extra_params_cannot_override_core_fields(self):
        messages = [{"role": "user", "content": "Return JSON."}]
        config = {
            "model_id": "qwen3:8b",
            "default_params": {"temperature": 0.25, "max_tokens": 1200},
            "param_overrides": {
                "top_p": 0.8,
                "model": "hijacked-model",
                "messages": [{"role": "user", "content": "hijacked"}],
                "stream": True,
            },
        }

        body = build_openai_chat_body(messages, config)

        self.assertEqual(body["model"], "qwen3:8b")
        self.assertEqual(body["messages"], messages)
        self.assertNotIn("stream", body)
        self.assertEqual(body["top_p"], 0.8)

    def test_deepseek_extra_params_use_same_reserved_field_rules(self):
        messages = [{"role": "user", "content": "Return JSON."}]
        config = {
            "model_id": "deepseek-v4-pro",
            "default_params": {"temperature": 0.35, "max_tokens": 2600},
            "param_overrides": {
                "reasoning_effort": "high",
                "response_format": {"type": "text"},
                "model": "hijacked-model",
            },
        }

        body = build_deepseek_chat_body(messages, config)

        self.assertEqual(body["model"], "deepseek-v4-pro")
        self.assertEqual(body["response_format"], {"type": "json_object"})
        self.assertEqual(body["reasoning_effort"], "high")


if __name__ == "__main__":
    unittest.main()
