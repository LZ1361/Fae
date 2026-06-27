import json
import unittest
from pathlib import Path


class RegistryTests(unittest.TestCase):
    def test_registry_has_deepseek_and_future_interfaces_without_secrets(self):
        path = Path("mingyun_app/model_registry.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        ids = {item["id"] for item in data["models"]}

        self.assertIn("deepseek-v4-pro", ids)
        self.assertIn("mock-local", ids)
        self.assertTrue(any(item["provider"] == "openai" for item in data["models"]))
        self.assertTrue(any(item["provider"] == "anthropic" for item in data["models"]))
        self.assertNotIn("sk-", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

