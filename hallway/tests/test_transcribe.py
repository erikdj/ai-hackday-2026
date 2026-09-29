"""Offline tests for local transcription. Live whisper runs only with RUN_WHISPER=1."""
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from hallway.ingest import transcribe as t

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "handoff_2.wav"


class _StubModel:
    def transcribe(self, path, beam_size=1, vad_filter=False):
        segments = [SimpleNamespace(text=" Okay, bed twelve. "), SimpleNamespace(text="  "),
                    SimpleNamespace(text="This is a synthetic patient.")]
        return iter(segments), SimpleNamespace(duration=90.0, language="en")


class TranscribeOfflineTests(unittest.TestCase):
    def test_joins_segments_and_reports_no_audio_leaving(self):
        with patch.object(t, "_model", return_value=_StubModel()):
            with tempfile.TemporaryDirectory() as d:
                audio = Path(d) / "x.wav"; audio.write_bytes(b"RIFF")
                result = t.transcribe(audio, "base")
        self.assertEqual(result["transcript"], "Okay, bed twelve. This is a synthetic patient.")
        self.assertEqual(result["audio_left_machine_bytes"], 0)
        self.assertEqual(result["audio_seconds"], 90.0)
        self.assertEqual(result["model"], "base")

    def test_to_inbox_writes_text_only_with_safe_name(self):
        with patch.object(t, "_model", return_value=_StubModel()):
            with tempfile.TemporaryDirectory() as d:
                audio = Path(d) / "hand off (2).wav"; audio.write_bytes(b"RIFF")
                target = t.to_inbox(audio, Path(d) / "inbox")
                self.assertEqual(target.name, "hand_off__2_.txt")
                self.assertEqual(target.read_text().strip(), "Okay, bed twelve. This is a synthetic patient.")
                self.assertEqual(sorted(p.name for p in target.parent.iterdir()), [target.name])

    def test_missing_file_fails_closed(self):
        with self.assertRaises(FileNotFoundError):
            t.transcribe("/nonexistent/recording.wav")

    @unittest.skipUnless(os.getenv("RUN_WHISPER") == "1" and FIXTURE.is_file(), "set RUN_WHISPER=1 for the live model")
    def test_live_fixture_contains_planted_lines(self):
        text = t.transcribe(FIXTURE, "base")["transcript"].lower()
        self.assertIn("callahan", text)
        self.assertIn("daughter", text)


if __name__ == "__main__":
    unittest.main()
