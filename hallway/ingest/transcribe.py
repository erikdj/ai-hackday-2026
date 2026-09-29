"""Local transcription for Safe Scribe: audio never leaves this machine.

faster-whisper runs on the presenting laptop (CPU, int8). Only the text it
produces is handed to Desk; the .wav bytes are read here and nowhere else.
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import time
from pathlib import Path

DEFAULT_MODEL = os.getenv("WHISPER_MODEL", "base")
_MODELS: dict[str, object] = {}
log = logging.getLogger("safescribe.ingest")


def _model(size: str):
    """Lazy per-size singleton so a demo pays the load cost once."""
    if size not in _MODELS:
        from faster_whisper import WhisperModel  # imported here so tests can stub it

        started = time.monotonic()
        _MODELS[size] = WhisperModel(size, device="cpu", compute_type="int8")
        log.info("whisper model=%s loaded in %.1fs (local, cpu)", size, time.monotonic() - started)
    return _MODELS[size]


def transcribe(path: str | Path, model_size: str | None = None) -> dict:
    """Transcribe one audio file locally. Returns text plus non-secret metadata."""
    audio = Path(path)
    if not audio.is_file():
        raise FileNotFoundError(f"audio file not found: {audio}")
    size = model_size or DEFAULT_MODEL
    started = time.monotonic()
    segments, info = _model(size).transcribe(str(audio), beam_size=1, vad_filter=False)
    text = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
    elapsed = round(time.monotonic() - started, 2)
    log.info("transcribed %s: %.0fs of audio, %d chars, %.1fs elapsed; 0 bytes of audio left this machine",
             audio.name, getattr(info, "duration", 0.0) or 0.0, len(text), elapsed)
    return {
        "transcript": text,
        "audio_seconds": round(float(getattr(info, "duration", 0.0) or 0.0), 1),
        "language": getattr(info, "language", None),
        "model": size,
        "elapsed_seconds": elapsed,
        "audio_left_machine_bytes": 0,
    }


def to_inbox(path: str | Path, inbox_dir: str | Path = "inbox", model_size: str | None = None) -> Path:
    """Transcribe and drop <stem>.txt into the inbox Desk watches. Never copies the audio."""
    audio = Path(path)
    stem = re.sub(r"[^A-Za-z0-9_-]", "_", audio.stem)[:80] or "recording"
    result = transcribe(audio, model_size)
    inbox = Path(inbox_dir)
    inbox.mkdir(parents=True, exist_ok=True)
    target = inbox / f"{stem}.txt"
    target.write_text(result["transcript"].strip() + "\n", encoding="utf-8")
    log.info("wrote %s (%d chars)", target, len(result["transcript"]))
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Transcribe a .wav locally and write the text to the inbox.")
    parser.add_argument("audio", help="path to a 16 kHz mono .wav, e.g. hallway/fixtures/handoff_2.wav")
    parser.add_argument("--inbox", default="inbox", help="directory Desk watches (default: inbox)")
    parser.add_argument("--model", default=None, help=f"faster-whisper size (default: {DEFAULT_MODEL})")
    parser.add_argument("--print", action="store_true", help="also print the transcript to stdout")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    target = to_inbox(args.audio, args.inbox, args.model)
    if args.print:
        print(target.read_text(encoding="utf-8"))
    print(f"inbox file: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
