"""Offline tests for the Brave research fact. Live only with RUN_BRAVE=1 and a key."""
import os
import unittest
from unittest.mock import patch

import httpx

from hallway.research import brave


class _Resp:
    def __init__(self, payload, status=200):
        self._payload, self.status_code = payload, status
    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("err", request=None, response=None)
    def json(self):
        return self._payload


class BraveOfflineTests(unittest.TestCase):
    def test_mock_when_no_key_is_labelled(self):
        with patch.dict(os.environ, {"BRAVE_API_KEY": "", "MOCK_BRAVE": "0"}, clear=False):
            f = brave.fact("warfarin")
        self.assertTrue(f["mock"]); self.assertEqual(f["source"], "mock"); self.assertIn("MOCK", f["title"])

    def test_live_picks_first_http_result_and_never_logs_key(self):
        payload = {"web": {"results": [{"url": "ftp://bad"}, {"url": "https://example.org/cipro", "title": "Cipro", "description": "Interaction."}]}}
        calls = {}
        def fake_get(self, url, params=None, headers=None):
            calls["headers"] = headers; return _Resp(payload)
        with patch.dict(os.environ, {"BRAVE_API_KEY": "secret-marker", "MOCK_BRAVE": "0"}, clear=False), \
             patch.object(httpx.Client, "get", fake_get), self.assertLogs("safescribe.research", level="INFO") as logs:
            f = brave.fact("ciprofloxacin")
        self.assertEqual(f["url"], "https://example.org/cipro"); self.assertFalse(f["mock"])
        self.assertEqual(calls["headers"]["X-Subscription-Token"], "secret-marker")
        self.assertNotIn("secret-marker", "\n".join(logs.output))

    def test_retries_then_none_on_failure(self):
        n = {"calls": 0}
        def boom(self, url, params=None, headers=None):
            n["calls"] += 1; raise httpx.ConnectError("down")
        with patch.dict(os.environ, {"BRAVE_API_KEY": "k", "MOCK_BRAVE": "0"}, clear=False), patch.object(httpx.Client, "get", boom):
            self.assertIsNone(brave.fact("warfarin", retries=2))
        self.assertEqual(n["calls"], 3)

    def test_empty_drug_rejected(self):
        with self.assertRaises(ValueError):
            brave.fact("  ")

    @unittest.skipUnless(os.getenv("RUN_BRAVE") == "1" and os.getenv("BRAVE_API_KEY"), "set RUN_BRAVE=1 with a key")
    def test_live_returns_sourced_url(self):
        f = brave.fact("ciprofloxacin")
        self.assertIsNotNone(f); self.assertTrue(f["url"].startswith("https://")); self.assertFalse(f["mock"])


if __name__ == "__main__":
    unittest.main()
