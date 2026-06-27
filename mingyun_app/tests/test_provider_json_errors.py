import unittest

from mingyun_app.providers.deepseek import parse_json_response


class ProviderJsonErrorTests(unittest.TestCase):
    def test_invalid_json_error_mentions_max_tokens(self):
        with self.assertRaisesRegex(RuntimeError, "max_tokens"):
            parse_json_response('{"title":"命运","dimensions":[{"claim":"未结束')


if __name__ == "__main__":
    unittest.main()

