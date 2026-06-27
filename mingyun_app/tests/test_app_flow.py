import unittest

from mingyun_app.app import create_reading_response, load_model_registry


class AppFlowTests(unittest.TestCase):
    def test_create_reading_response_returns_rich_evidence_and_mock_reading(self):
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
                "model_id": "mock-local",
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
        self.assertEqual(response["model"], "mock-local")
        self.assertEqual(response["evidence_profile"]["western_zodiac"]["sign"], "金牛座")
        self.assertEqual(response["evidence_profile"]["bazi"]["pillars"]["day"]["pillar"], "癸丑")
        self.assertIn("chart_overview", response["reading"])
        self.assertIn("plain_takeaways", response["reading"])
        self.assertIn("direct_answer", response["reading"]["plain_takeaways"])
        self.assertIn("life_topics", response["reading"])
        self.assertIn("relationship_profile", response["reading"])
        self.assertIn("matchmaking", response["reading"])
        self.assertGreaterEqual(len(response["reading"]["life_topics"]), 6)


if __name__ == "__main__":
    unittest.main()
