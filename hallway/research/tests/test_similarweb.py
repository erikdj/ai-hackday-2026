"""Similarweb spoken-domain and organization-fact tests."""

import os
import unittest
import urllib.error
from unittest.mock import patch

from hallway.research.similarweb import fact_from_transcript, organization_fact, spoken_domain

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

    def test_stops_at_boundary_words(self):
        self.assertEqual(spoken_domain("Their website is example dot org"), "example.org")

    def test_phrase_with_and_without_name(self):
        self.assertEqual(spoken_domain(PHRASE), "sunrisehomehealth.com")
        self.assertEqual(spoken_domain(PHRASE, "Sunrise Home Health"), "sunrisehomehealth.com")

    def test_name_path_ignores_leading_words(self):
        text = "you can look at sunrise home health dot com later"
        self.assertEqual(spoken_domain(text, "Sunrise Home Health"), "sunrisehomehealth.com")

    def test_hyphenated_label_matches_spaced_name(self):
        self.assertEqual(
            spoken_domain("Their website is acme-care dot org", "Acme Care"),
            "acme-care.org",
        )

    def test_name_rejects_domain_suffix(self):
        self.assertIsNone(spoken_domain("sunrise home health dot com", "Home Health"))

    def test_care_dot_health(self):
        self.assertEqual(spoken_domain("go to acme care dot health"), "acmecare.health")

    def test_text_without_domain_is_none(self):
        self.assertIsNone(spoken_domain("nothing spoken here about a site"))

    def test_named_org_ignores_unrelated_spoken_domain(self):
        text = (
            "Visit example dot org for general information. "
            "Referral to Sunrise Home Health."
        )
        self.assertIsNone(spoken_domain(text, "Sunrise Home Health"))
        with patch.dict(os.environ, {"MOCK_SIMILARWEB": "1"}):
            self.assertIsNone(fact_from_transcript(text, "Sunrise Home Health"))


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

    def test_rank_zero_with_visits_is_unranked(self):
        def fetch(url):
            if "similar-rank" in url:
                return {"similar_rank": {"rank": 0}}
            return {"visits": [{"date": "2026-08-01", "visits": 890}]}

        with _live_env():
            fact = organization_fact("Tiny Clinic", "tiny.example", fetch=fetch)
        self.assertIsNone(fact["rank"])
        self.assertEqual(fact["monthly_visits"], 890)
        self.assertTrue(fact["low_traffic"])
        self.assertEqual(fact["status"], "active")
        self.assertIn("not in Similarweb's global ranking", fact["claim"])
        self.assertIn("890", fact["claim"])

    def test_rank_404_is_not_found(self):
        def fetch(url):
            if "similar-rank" in url:
                raise urllib.error.HTTPError(url, 404, "missing", None, None)
            raise AssertionError(url)

        with _live_env():
            fact = organization_fact("Ghost Clinic", "missing.example", fetch=fetch)
        self.assertFalse(fact["active"])
        self.assertEqual(fact["status"], "not_found")
        self.assertIsNone(fact["rank"])
        self.assertIsNone(fact["monthly_visits"])
        self.assertIsNone(fact["low_traffic"])
        self.assertIn("not listed on Similarweb", fact["claim"])

    def test_empty_payloads_fail_closed(self):
        with _live_env():
            self.assertIsNone(
                organization_fact("Sunrise Home Health", "example.com", fetch=lambda url: {})
            )

    def test_rank_only_keeps_fact(self):
        def fetch(url):
            if "similar-rank" in url:
                return {"similar_rank": {"rank": 42}}
            return {"visits": []}

        with _live_env():
            fact = organization_fact("Example", "example.org", fetch=fetch)
        self.assertIsNotNone(fact)
        self.assertEqual(fact["rank"], 42)
        self.assertIsNone(fact["monthly_visits"])
        self.assertTrue(fact["active"])
        self.assertIn("visit count unavailable", fact["claim"])


if __name__ == "__main__":
    unittest.main()
