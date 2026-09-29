"""Offline tests for the upload page; transcription is stubbed."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from hallway.ingest import upload


class UploadTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.inbox = Path(self.dir.name) / "inbox"
        self.patch = patch.object(upload, "INBOX", self.inbox); self.patch.start()
        self.client = TestClient(upload.app)

    def tearDown(self):
        self.patch.stop(); self.dir.cleanup()

    def test_index_says_audio_stays_local(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200); self.assertIn("transcribed on this laptop", r.text)

    def test_txt_lands_in_inbox_with_safe_name(self):
        r = self.client.post("/upload", files={"file": ("hand off 2.txt", b"Okay, bed twelve.\n", "text/plain")})
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json(); self.assertEqual(body["source"], "text")
        self.assertEqual(Path(body["inbox_file"]).read_text().strip(), "Okay, bed twelve.")
        self.assertEqual(Path(body["inbox_file"]).name, "hand_off_2.txt")

    def test_wav_is_transcribed_and_not_kept(self):
        fake = {"transcript": "This is a synthetic patient.", "audio_seconds": 90.0, "model": "base", "elapsed_seconds": 1.0}
        with patch.object(upload, "transcribe", return_value=fake):
            r = self.client.post("/upload", files={"file": ("handoff_2.wav", b"RIFF....", "audio/wav")})
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json(); self.assertEqual(body["source"], "wav"); self.assertEqual(body["audio_left_machine_bytes"], 0)
        self.assertEqual(sorted(p.name for p in self.inbox.iterdir()), ["handoff_2.txt"])

    def test_rejects_other_types_and_empty(self):
        self.assertEqual(self.client.post("/upload", files={"file": ("x.pdf", b"%PDF", "application/pdf")}).status_code, 415)
        self.assertEqual(self.client.post("/upload", files={"file": ("x.txt", b"", "text/plain")}).status_code, 400)


if __name__ == "__main__":
    unittest.main()
