"""MCP JSON-RPC tests. Neo4j is the in-memory store."""

import asyncio
import os
import unittest
from unittest.mock import patch

try:
    from fastapi.testclient import TestClient
except Exception:  # httpx missing
    TestClient = None


def _seed(store):
    store.reset()
    store.write_approved(
        {
            "follow_ups": [
                {"owner": "Nurse", "text": "call", "status": "owned"},
                {"text": "labs"},
            ]
        },
        [
            {"agent": "Desk", "field": "patient_name"},
            {"agent": "Scribe", "field": "dob"},
            {"agent": "Critic", "field": "mrn"},
            {"agent": "Grapher", "field": "meds"},
        ],
        "pseudo-1",
        "enc-1",
    )


class McpHandleTests(unittest.TestCase):
    def setUp(self):
        self._env = patch.dict(os.environ, {"MOCK_NEO4J": "1"})
        self._env.start()
        from hallway.dashboard import mcp, queries
        from hallway.graph import store

        self.mcp = mcp
        self.queries = queries
        self.store = store
        _seed(store)

    def tearDown(self):
        self.store.reset()
        self._env.stop()

    def test_initialize_server_info(self):
        response = self.mcp.handle(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18"},
            }
        )
        self.assertEqual(response["result"]["serverInfo"]["name"], "safe-scribe-lineage")
        self.assertEqual(response["result"]["protocolVersion"], "2025-06-18")

    def test_tools_list_names(self):
        response = self.mcp.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        names = [tool["name"] for tool in response["result"]["tools"]]
        self.assertEqual(
            names,
            ["who_saw_identifiers", "open_followups_by_owner", "patient_history"],
        )

    def test_who_saw_matches_queries(self):
        response = self.mcp.handle(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "who_saw_identifiers", "arguments": {}},
            }
        )
        body = response["result"]
        self.assertFalse(body["isError"])
        expected = {
            k: v
            for k, v in self.queries.who_saw_identifiers().items()
            if k not in ("expected_on_demo", "matches_expected")
        }
        self.assertEqual(body["structuredContent"], expected)
        text = body["content"][0]["text"]
        for key in ("expected_on_demo", "matches_expected"):
            self.assertNotIn(key, body["structuredContent"])
            self.assertNotIn(key, text)

    def test_followups_owner_filter(self):
        response = self.mcp.handle(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "open_followups_by_owner",
                    "arguments": {"owner": "nurse"},
                },
            }
        )
        self.assertEqual(response["result"]["structuredContent"], {"Nurse": ["call"]})

    def test_unknown_tool(self):
        response = self.mcp.handle(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {"name": "nope", "arguments": {}},
            }
        )
        self.assertTrue(response["result"]["isError"])

    def test_unknown_method(self):
        response = self.mcp.handle({"jsonrpc": "2.0", "id": 6, "method": "nope"})
        self.assertEqual(response["error"]["code"], -32601)

    def test_notification_returns_none(self):
        self.assertIsNone(
            self.mcp.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
        )

    @unittest.skipUnless(TestClient is not None, "fastapi.testclient needs httpx")
    def test_http_initialize(self):
        from hallway.dashboard.app import create_app

        client = TestClient(create_app())
        response = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["result"]["serverInfo"]["name"],
            "safe-scribe-lineage",
        )

    @unittest.skipUnless(TestClient is not None, "fastapi.testclient needs httpx")
    def test_dispatch_runs_off_event_loop(self):
        from hallway.dashboard.app import create_app

        off_loop = []

        def fake_handle(_message):
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                off_loop.append(True)
            else:
                off_loop.append(False)
            return {"jsonrpc": "2.0", "id": 1, "result": {}}

        client = TestClient(create_app())
        ping = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
        with patch("hallway.dashboard.mcp.handle", fake_handle):
            single = client.post("/mcp", json=ping)
            batch = client.post("/mcp", json=[ping, ping])
        self.assertEqual(single.status_code, 200)
        self.assertEqual(batch.status_code, 200)
        self.assertEqual(off_loop, [True, True, True])
