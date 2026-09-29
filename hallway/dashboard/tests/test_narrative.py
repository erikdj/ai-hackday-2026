"""Compliance narrative: only allowlisted metadata reaches the model; fail closed otherwise."""

import json
import os
import unittest
from unittest.mock import patch

from hallway.dashboard import narrative
from hallway.graph import store

PATIENT_NAME = "Robert Callahan"
DOB = "March fourth, nineteen fifty-two"
REPLY = "Desk, Scribe and Critic processed identifiers. Others did not. Records are pseudonymous."


class _FakeChat:
    def __init__(self, reply=REPLY, model="Qwen/Qwen3.8-27B"):
        self.reply = reply
        self.model = model
        self.messages = None

    def __call__(self, messages):
        self.messages = messages
        return self.reply, self.model


def _seed():
    store.reset()
    # Brief values deliberately carry identifier-looking text so a leak would be visible.
    store.write_approved(
        {"follow_ups": [{"owner": "Nurse", "text": f"call {PATIENT_NAME}", "status": "owned"}, {"text": "labs"}],
         "findings": [{"text": f"born {DOB}"}]},
        [
            {"agent": "desk", "field": "patient_name", "purpose": "intake"},
            {"agent": "desk", "field": "dob", "purpose": "intake"},
            {"agent": "scribe", "field": "patient_name", "purpose": "extraction"},
            {"agent": "critic", "field": "dob", "purpose": "review"},
            {"agent": "grapher", "field": "brief", "purpose": "graph_write"},
            {"agent": "researcher", "field": "brief", "purpose": "extraction"},
        ],
        f"p_{PATIENT_NAME.replace(' ', '')}",
        "enc-1",
    )


class NarrativeTests(unittest.TestCase):
    def setUp(self):
        self._env = patch.dict(os.environ, {"MOCK_NEO4J": "1"})
        self._env.start()
        _seed()

    def tearDown(self):
        store.reset()
        self._env.stop()

    def test_inputs_are_names_fields_and_counts_only(self):
        inputs = narrative.narrative_inputs()
        self.assertEqual(inputs["agents_with_identifier_access"], ["Critic", "Desk", "Scribe"])
        self.assertEqual(inputs["identifier_fields_by_agent"]["Desk"], ["dob", "patient_name"])
        self.assertEqual(inputs["agents_without_identifier_access"], ["Grapher"])
        # A PHI-side processing row with no identifier rows is unverified, never "no access".
        self.assertEqual(inputs["agents_with_unverified_identifier_evidence"], ["Researcher"])
        self.assertEqual(inputs["pseudonymous_patients"], 1)
        blob = json.dumps(inputs)
        for forbidden in (PATIENT_NAME, "Callahan", DOB, "p_Robert", "enc-1", "labs"):
            self.assertNotIn(forbidden, blob)

    def test_model_sees_exactly_the_inputs_and_result_echoes_them(self):
        chat = _FakeChat()
        result = narrative.compliance_narrative(chat=chat)
        self.assertEqual(chat.messages[0]["role"], "system")
        sent = chat.messages[1]["content"]
        self.assertEqual(json.loads(sent), result["inputs"])
        self.assertNotIn("Callahan", sent)
        self.assertEqual(result["provider"], "crusoe")
        self.assertEqual(result["model"], "Qwen/Qwen3.8-27B")
        self.assertTrue(result["narrative"].startswith("Desk, Scribe and Critic"))

    def test_model_name_comes_from_the_completion(self):
        result = narrative.compliance_narrative(chat=_FakeChat(model="deepseek-ai/Deepseek-V4-Flash"))
        self.assertEqual(result["model"], "deepseek-ai/Deepseek-V4-Flash")

    def test_empty_model_reply_fails_closed(self):
        with self.assertRaises(narrative.NarrativeUnavailable):
            narrative.compliance_narrative(chat=_FakeChat(reply=""))

    def test_unsafe_agent_names_are_dropped(self):
        store.write_approved({}, [{"agent": f"{PATIENT_NAME} <script>", "field": "dob"}], "p_x", "enc-2")
        inputs = narrative.narrative_inputs()
        self.assertNotIn("Callahan", json.dumps(inputs))

    def test_non_crusoe_endpoint_is_refused(self):
        with patch.dict(os.environ, {"CRUSOE_BASE_URL": "https://example.invalid/v1", "CRUSOE_API_KEY": "k", "CRUSOE_MODEL_FAST": "m"}):
            with self.assertRaises(ValueError):
                narrative.crusoe_chat([{"role": "user", "content": "x"}])


if __name__ == "__main__":
    unittest.main()
