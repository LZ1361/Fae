import unittest

from mingyun_app.core.inference import build_evidence_profile


class InferenceTests(unittest.TestCase):
    def test_builds_explainable_profile_with_full_bazi_context(self):
        profile = build_evidence_profile(
            {
                "birth_date": "1998-05-06",
                "birth_time": "14:30",
                "birth_time_accuracy": "accurate",
                "birth_city": "上海",
                "gender": "female",
                "calendar_type": "solar",
                "focus_theories": ["MBTI", "天干地支", "星座", "五行"],
                "psychology_answers": {
                    "energy_social": 2,
                    "planning": 4,
                    "emotion_focus": 3,
                    "novelty": 4,
                },
            }
        )

        self.assertEqual(profile["western_zodiac"]["sign"], "金牛座")
        self.assertEqual(profile["input_summary"]["gender"], "female")
        self.assertEqual(profile["bazi"]["pillars"]["year"]["pillar"], "戊寅")
        self.assertEqual(profile["bazi"]["pillars"]["month"]["pillar"], "丁巳")
        self.assertEqual(profile["bazi"]["pillars"]["hour"]["branch"], "未")
        self.assertIsNotNone(profile["bazi"]["pillars"]["day"]["pillar"])
        self.assertEqual(profile["bazi"]["zodiac"]["animal"], "虎")
        self.assertEqual(profile["bazi"]["solar_term"]["current"]["name"], "立夏")
        self.assertIn("寅", profile["bazi"]["hidden_stems"])
        self.assertTrue(profile["ten_gods"]["day_master"]["stem"])
        self.assertTrue(profile["ten_gods"]["distribution"])
        self.assertIn("relationship_profile", profile)
        self.assertIn("matchmaking", profile)
        self.assertEqual(profile["matchmaking"]["target_gender"], "male")
        self.assertTrue(profile["matchmaking"]["recommended_elements"])
        self.assertIn("relationship", profile["life_topics"])
        self.assertIn("career", profile["life_topics"])
        self.assertIn("wealth", profile["life_topics"])
        self.assertGreaterEqual(profile["confidence"]["overall"], 0.65)
        self.assertTrue(profile["evidence"])
        self.assertTrue(profile["limits"])

    def test_uncertain_birth_time_keeps_day_pillar_but_lowers_hour_confidence(self):
        profile = build_evidence_profile(
            {
                "birth_date": "2001-11-23",
                "birth_time": "",
                "birth_time_accuracy": "unknown",
                "birth_city": "成都",
                "calendar_type": "solar",
                "focus_theories": ["天干地支", "五行"],
                "psychology_answers": {},
            }
        )

        self.assertIsNone(profile["bazi"]["pillars"]["hour"]["branch"])
        self.assertIsNone(profile["bazi"]["pillars"]["hour"]["pillar"])
        self.assertIsNotNone(profile["bazi"]["pillars"]["day"]["pillar"])
        self.assertLess(profile["confidence"]["time_sensitive"], 0.5)
        self.assertIn("出生时间不确定", " ".join(profile["limits"]))


if __name__ == "__main__":
    unittest.main()
