import unittest
from datetime import date

from mingyun_app.core.inference import build_evidence_profile
from mingyun_app.core.lunar_calendar import lunar_to_solar


class LunarCalendarTests(unittest.TestCase):
    def test_lunar_new_year_2024_converts_to_solar(self):
        self.assertEqual(lunar_to_solar(2024, 1, 1), date(2024, 2, 10))

    def test_mid_autumn_2023_converts_to_solar(self):
        self.assertEqual(lunar_to_solar(2023, 8, 15), date(2023, 9, 29))

    def test_lunar_birth_date_is_converted_before_bazi_calculation(self):
        profile = build_evidence_profile(
            {
                "birth_date": "2024-01-01",
                "birth_time": "09:30",
                "birth_time_accuracy": "accurate",
                "birth_city": "北京",
                "gender": "female",
                "calendar_type": "lunar",
                "lunar_is_leap": False,
                "focus_theories": ["天干地支", "五行"],
                "psychology_answers": {},
            }
        )

        self.assertEqual(profile["input_summary"]["calendar_type"], "lunar")
        self.assertEqual(profile["input_summary"]["birth_date"], "2024-01-01")
        self.assertEqual(profile["input_summary"]["solar_birth_date"], "2024-02-10")
        self.assertIn("农历", profile["input_summary"]["calendar_conversion"]["basis"])
        self.assertEqual(profile["bazi"]["zodiac"]["animal"], "龙")


if __name__ == "__main__":
    unittest.main()
