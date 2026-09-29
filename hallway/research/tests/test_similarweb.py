"""Similarweb spoken-domain and organization-fact tests."""

import os
import unittest
import urllib.error
from unittest.mock import patch

from hallway.research.similarweb import organization_fact, spoken_domain

PHRASE = "she found a place called Sunrise Home Health, sunrise home health dot com."


def _live_env(**extra):
    env = {"SIMILARWEB_API_KEY": "test-key", "MOCK_SIMILARWEB": "0"}
    env.update(extra)
    return patch.dict(os.environ, env)


class SpokenDomainTest(unittest.TestCase):
    def test_fixture_phrase(self):
        self.assertEqual(spoken_domain(PHRASE), "sunrisehomehealth.com")

    def test_no_domain(self):
        self.assertIsNone(spoken_domain("she found a place called Sunrise Home Health."))


class OrganizationFactTest(unittest.TestCase):
    def test_mock_flag(self):
        with patch.dict(os.environ, {"MOCK_SIMILARWEB": "1"}):
            fact = organization_fact("Sunrise Home Health", "sunrisehomehealth.com")
        self.assertIsNotNone(fact)
        self.assertTrue(fact["url"].startswith("https://"))
        self.assertIn("Sunrise Home Health", fact["claim"])
        self.assertIn("sunrisehomehealth.com", fact["claim"])
        self.assertNotIn("api_key", fact["claim"])

    def test_missing_key(self):
        with patch.dict(os.environ, {"SIMILARWEB_API_KEY": "", "MOCK_SIMILARWEB": "0"}):
            self.assertIsNone(organization_fact("Sunrise Home Health", "sunrisehomehealth.com"))

    def test_stub_formats_numbers(self):
        def fetch(url):
            if "similar-rank" in url:
                return {"similar_rank": {"rank": 1234567}}
            return {"visits": [{"date": "2026-08-01", "visits": 12000.0}]}

        with _live_env():
            fact = organization_fact("Sunrise Home Health", "sunrisehomehealth.com", fetch=fetch)
        self.assertEqual(fact["rank"], 1234567)
        self.assertEqual(fact["monthly_visits"], 12000)
        self.assertEqual(fact["month"], "2026-08")
        self.assertIn("1,234,567", fact["claim"])
        self.assertIn("12,000", fact["claim"])
        self.assertNotIn("test-key", fact["url"])
        self.assertNotIn("test-key", fact["claim"])

    def test_http_429(self):
        def fetch(url):
            raise urllib.error.HTTPError(url, 429, "rate", None, None)

        with _live_env():
            self.assertIsNone(organization_fact("Sunrise Home Health", "example.com", fetch=fetch))

    def test_urlerror_retries(self):
        calls = {"n": 0}

        def fetch(url):
            calls["n"] += 1
            if calls["n"] <= 2:
                raise urllib.error.URLError("temporary")
            if "similar-rank" in url:
                return {"similar_rank": {"rank": 10}}
            return {"visits": [{"date": "2026-08-01", "visits": 5}]}

        with _live_env():
            fact = organization_fact("Example", "example.org", fetch=fetch)
        self.assertIsNotNone(fact)
        self.assertEqual(fact["rank"], 10)
        self.assertGreaterEqual(calls["n"], 3)


if __name__ == "__main__":
    unittest.main()
