import unittest

from mingyun_app.core.prompts import build_reading_prompt


class PromptTests(unittest.TestCase):
    def test_prompt_requires_json_and_forbids_fabrication(self):
        prompt = build_reading_prompt(
            {
                "evidence_profile": {"evidence": [{"label": "太阳星座", "value": "金牛座"}]},
                "style": "balanced",
                "mysticism_level": 50,
            }
        )

        joined = "\n".join(message["content"] for message in prompt)
        self.assertIn("json", joined.lower())
        self.assertIn("不得编造", joined)
        self.assertIn("依据", joined)
        self.assertIn("置信度", joined)

    def test_prompt_requires_rich_report_sections(self):
        prompt = build_reading_prompt(
            {
                "evidence_profile": {
                    "bazi": {"pillars": {}},
                    "life_topics": {"career": {"title": "事业"}},
                },
                "style": "rational",
                "mysticism_level": 20,
            }
        )

        joined = "\n".join(message["content"] for message in prompt)
        self.assertIn("chart_overview", joined)
        self.assertIn("life_topics", joined)
        self.assertIn("questions_to_reflect", joined)
        self.assertIn("relationship_profile", joined)
        self.assertIn("matchmaking", joined)
        self.assertIn("plain_takeaways", joined)
        self.assertIn("直白", joined)
        self.assertIn("少用术语", joined)


if __name__ == "__main__":
    unittest.main()
