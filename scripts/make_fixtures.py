#!/usr/bin/env python3
"""Build Safe Scribe demo fixtures: two-speaker scenario scripts -> transcript .txt + 16 kHz mono .wav.

Usage:
    python3 scripts/make_fixtures.py                 # all scripts in scripts/fixtures/
    python3 scripts/make_fixtures.py handoff_2          # one scenario
    python3 scripts/make_fixtures.py --txt-only      # no network, no audio

Script format (scripts/fixtures/<name>.script):
    # voices: A=eve B=leo                       (xAI voice ids)
    # edge-voices: A=en-US-JennyNeural B=en-US-GuyNeural   (no-key fallback)
    A: first line spoken by speaker A
    B: reply from speaker B

TTS vendor: xAI (`POST https://api.x.ai/v1/tts`, voices eve/ara/rex/sal/leo/grok) when
XAI_API_KEY is set in the environment or .env, else Microsoft neural voices via `edge-tts`
(free, no key). `synthesize_line` is the only place that knows about vendors.
Needs `ffmpeg` on PATH to normalise to 16 kHz mono. Output goes to hallway/fixtures/.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
import wave
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO / "scripts" / "fixtures"
OUT_DIR = REPO / "hallway" / "fixtures"
SAMPLE_RATE = 16_000
SPEECH_RATE = "+12%"  # handoffs are brisk; also keeps the demo clip near a minute
GAP_SECONDS = 0.45
DEFAULT_VOICES = {"A": "eve", "B": "leo"}
EDGE_VOICES = {"A": "en-US-JennyNeural", "B": "en-US-GuyNeural"}
XAI_TTS_URL = "https://api.x.ai/v1/tts"
LINE_RE = re.compile(r"^([A-Z]):\s*(.+?)\s*$")


@dataclass(frozen=True)
class Line:
    speaker: str
    text: str


@dataclass(frozen=True)
class Script:
    name: str
    voices: dict[str, str]        # xAI voice ids
    edge_voices: dict[str, str]   # edge-tts voice names (no-key fallback)
    lines: tuple[Line, ...]


def parse_script(name: str, raw: str) -> Script:
    voices = dict(DEFAULT_VOICES)
    edge_voices = dict(EDGE_VOICES)
    lines: list[Line] = []
    for n, row in enumerate(raw.splitlines(), 1):
        row = row.strip()
        if not row:
            continue
        header = {"# voices:": voices, "# edge-voices:": edge_voices}
        prefix = next((k for k in header if row.startswith(k)), None)
        if prefix:
            for pair in row[len(prefix):].split():
                speaker, _, voice = pair.partition("=")
                if speaker and voice:
                    header[prefix][speaker] = voice
            continue
        if row.startswith("#"):
            continue
        m = LINE_RE.match(row)
        if not m:
            raise ValueError(f"{name}:{n}: expected 'X: text', got {row!r}")
        lines.append(Line(m.group(1), m.group(2)))
    if not lines:
        raise ValueError(f"{name}: no dialogue lines")
    missing = {ln.speaker for ln in lines} - (voices.keys() & edge_voices.keys())
    if missing:
        raise ValueError(f"{name}: no voice for speaker(s) {sorted(missing)}")
    return Script(name, voices, edge_voices, tuple(lines))


def transcript_text(script: Script) -> str:
    """What faster-whisper would roughly produce: spoken text only, no speaker labels."""
    return "\n".join(ln.text for ln in script.lines) + "\n"


def load_dotenv() -> None:
    path = REPO / ".env"
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip("'\"")
        if key and not os.environ.get(key):
            os.environ[key] = value


def tts_vendor() -> str:
    return "xai" if os.environ.get("XAI_API_KEY") else "edge"


def xai_tts(text: str, voice: str, out_path: Path) -> None:
    body = json.dumps({"text": text, "voice_id": voice, "language": "en",
                       "output_format": {"codec": "wav"}}).encode()
    req = urllib.request.Request(
        XAI_TTS_URL, data=body, method="POST",
        headers={"Authorization": f"Bearer {os.environ['XAI_API_KEY']}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        out_path.write_bytes(resp.read())


async def edge_tts_line(text: str, voice: str, out_path: Path) -> None:
    import edge_tts  # imported here so --txt-only and tests need no network package

    await edge_tts.Communicate(text, voice, rate=SPEECH_RATE).save(str(out_path))


async def synthesize_line(text: str, voice: str, out_path: Path) -> None:
    """Write one spoken line as audio (any container ffmpeg can read)."""
    if tts_vendor() == "xai":
        await asyncio.to_thread(xai_tts, text, voice, out_path)
    else:
        await edge_tts_line(text, voice, out_path)
    if not out_path.is_file() or out_path.stat().st_size == 0:
        raise RuntimeError(f"{tts_vendor()} TTS produced no audio for voice {voice}")


def to_wav16k(src: Path, wav_path: Path) -> None:
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
           "-ar", str(SAMPLE_RATE), "-ac", "1", "-sample_fmt", "s16", str(wav_path)]
    subprocess.run(cmd, check=True, timeout=60)


def stitch_wavs(parts: list[Path], out_path: Path, gap_seconds: float = GAP_SECONDS) -> float:
    """Concatenate 16 kHz mono s16 wavs with silence between; returns duration in seconds."""
    silence = b"\x00\x00" * int(SAMPLE_RATE * gap_seconds)
    frames = 0
    with wave.open(str(out_path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(SAMPLE_RATE)
        for i, part in enumerate(parts):
            with wave.open(str(part), "rb") as w:
                if (w.getnchannels(), w.getsampwidth(), w.getframerate()) != (1, 2, SAMPLE_RATE):
                    raise ValueError(f"{part}: expected 16 kHz mono s16")
                data = w.readframes(w.getnframes())
            if i:
                out.writeframes(silence)
                frames += len(silence) // 2
            out.writeframes(data)
            frames += len(data) // 2
    return frames / SAMPLE_RATE


async def build_audio(script: Script, wav_path: Path) -> float:
    with tempfile.TemporaryDirectory(dir=wav_path.parent) as tmp:  # snap ffmpeg cannot read /tmp
        tmp_dir = Path(tmp)
        parts: list[Path] = []
        voices = script.voices if tts_vendor() == "xai" else script.edge_voices
        for i, ln in enumerate(script.lines):
            raw = tmp_dir / f"{i:03d}.raw"
            part = tmp_dir / f"{i:03d}.wav"
            await synthesize_line(ln.text, voices[ln.speaker], raw)
            to_wav16k(raw, part)
            parts.append(part)
        return stitch_wavs(parts, wav_path)


def build(script: Script, out_dir: Path, txt_only: bool) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{script.name}.txt").write_text(transcript_text(script), encoding="utf-8")
    words = sum(len(ln.text.split()) for ln in script.lines)
    msg = f"{script.name}: {len(script.lines)} lines, {words} words -> {script.name}.txt"
    if not txt_only:
        seconds = asyncio.run(build_audio(script, out_dir / f"{script.name}.wav"))
        msg += f", {script.name}.wav ({seconds:.1f}s, {tts_vendor()} voices)"
    print(msg)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("names", nargs="*", help="scenario names (default: all)")
    parser.add_argument("--txt-only", action="store_true", help="write transcripts only, no TTS")
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args(argv)
    load_dotenv()
    paths = sorted(SCRIPTS_DIR.glob("*.script"))
    if args.names:
        paths = [p for p in paths if p.stem in set(args.names)]
        unknown = set(args.names) - {p.stem for p in paths}
        if unknown:
            print(f"unknown scenario(s): {sorted(unknown)}", file=sys.stderr)
            return 2
    if not paths:
        print(f"no .script files in {SCRIPTS_DIR}", file=sys.stderr)
        return 2
    for path in paths:
        try:
            build(parse_script(path.stem, path.read_text(encoding="utf-8")), args.out, args.txt_only)
        except (ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
            print(f"{path.stem}: {exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
