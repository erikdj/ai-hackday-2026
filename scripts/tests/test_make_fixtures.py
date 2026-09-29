"""Tests for scripts/make_fixtures.py. No network, no ffmpeg."""

import importlib.util
import sys
import wave
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "make_fixtures.py"


def _load():
    spec = importlib.util.spec_from_file_location("make_fixtures", _SRC)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # dataclasses resolve annotations via sys.modules
    spec.loader.exec_module(mod)
    return mod


def _write_wav(path: Path, seconds: float, rate: int = 16_000) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x01\x00" * int(rate * seconds))


def test_parse_script_voices_and_lines():
    mod = _load()
    raw = "# voices: A=en-US-AriaNeural B=en-US-EricNeural\n# comment\n\nA: Hello there.\nB: Hi.\n"
    s = mod.parse_script("demo", raw)
    assert s.voices == {"A": "en-US-AriaNeural", "B": "en-US-EricNeural"}
    assert [(ln.speaker, ln.text) for ln in s.lines] == [("A", "Hello there."), ("B", "Hi.")]


def test_parse_script_defaults_and_errors():
    mod = _load()
    s = mod.parse_script("d", "A: one\nB: two\n")
    assert s.voices == mod.DEFAULT_VOICES
    with pytest.raises(ValueError, match="expected 'X: text'"):
        mod.parse_script("d", "A: ok\nnot a line\n")
    with pytest.raises(ValueError, match="no dialogue"):
        mod.parse_script("d", "# only a comment\n")
    with pytest.raises(ValueError, match="no voice for speaker"):
        mod.parse_script("d", "C: who speaks this\n")


def test_transcript_has_no_speaker_labels():
    mod = _load()
    s = mod.parse_script("d", "A: Bed twelve.\nB: Got it.\n")
    text = mod.transcript_text(s)
    assert text == "Bed twelve.\nGot it.\n"
    assert "A:" not in text and "B:" not in text


def test_stitch_wavs_inserts_gaps(tmp_path):
    mod = _load()
    a, b = tmp_path / "a.wav", tmp_path / "b.wav"
    _write_wav(a, 1.0)
    _write_wav(b, 0.5)
    out = tmp_path / "out.wav"
    seconds = mod.stitch_wavs([a, b], out, gap_seconds=0.5)
    assert seconds == pytest.approx(2.0, abs=0.01)
    with wave.open(str(out)) as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, 16_000)


def test_stitch_wavs_rejects_wrong_rate(tmp_path):
    mod = _load()
    bad = tmp_path / "bad.wav"
    _write_wav(bad, 0.2, rate=44_100)
    with pytest.raises(ValueError, match="16 kHz mono"):
        mod.stitch_wavs([bad], tmp_path / "out.wav")


def test_txt_only_end_to_end(tmp_path, monkeypatch, capsys):
    mod = _load()
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "handoff_9.script").write_text("A: Alpha.\nB: Beta.\n", encoding="utf-8")
    monkeypatch.setattr(mod, "SCRIPTS_DIR", scripts)
    out = tmp_path / "out"
    assert mod.main(["--txt-only", "--out", str(out)]) == 0
    assert (out / "handoff_9.txt").read_text(encoding="utf-8") == "Alpha.\nBeta.\n"
    assert not (out / "handoff_9.wav").exists()
    assert mod.main(["--txt-only", "--out", str(out), "nope"]) == 2
    capsys.readouterr()


def test_edge_voices_header_and_vendor_selection(monkeypatch):
    mod = _load()
    raw = "# voices: A=ara B=rex\n# edge-voices: A=en-US-AriaNeural\nA: x\nB: y\n"
    s = mod.parse_script("d", raw)
    assert s.voices == {"A": "ara", "B": "rex"}
    assert s.edge_voices == {"A": "en-US-AriaNeural", "B": mod.EDGE_VOICES["B"]}
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    assert mod.tts_vendor() == "edge"
    monkeypatch.setenv("XAI_API_KEY", "x")
    assert mod.tts_vendor() == "xai"


def test_dotenv_does_not_override_environment(tmp_path, monkeypatch):
    mod = _load()
    (tmp_path / ".env").write_text("XAI_API_KEY=filekey\nOTHER_KEY='quoted'\n", encoding="utf-8")
    monkeypatch.setattr(mod, "REPO", tmp_path)
    monkeypatch.setenv("XAI_API_KEY", "envkey")
    monkeypatch.delenv("OTHER_KEY", raising=False)
    mod.load_dotenv()
    assert mod.os.environ["XAI_API_KEY"] == "envkey"
    assert mod.os.environ["OTHER_KEY"] == "quoted"
