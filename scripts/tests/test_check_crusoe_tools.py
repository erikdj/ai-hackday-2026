"""Tests for scripts/check_crusoe_tools.py. No network."""

import importlib.util
import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_SRC = _REPO / "scripts" / "check_crusoe_tools.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_crusoe_tools", _SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def mod():
    return _load()


def _point_env_root(mod, monkeypatch, root: Path) -> None:
    scripts = root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(mod, "__file__", str(scripts / "x.py"))


def test_dotenv_defaults_only(tmp_path, monkeypatch):
    mod = _load()
    (tmp_path / ".env").write_text(
        "CRUSOE_API_KEY=filekey\nCRUSOE_MODEL=filemodel\n", encoding="utf-8"
    )
    _point_env_root(mod, monkeypatch, tmp_path)
    monkeypatch.setenv("CRUSOE_API_KEY", "callerkey")
    monkeypatch.delenv("CRUSOE_MODEL", raising=False)
    mod.load_dotenv()
    assert mod.os.environ["CRUSOE_API_KEY"] == "callerkey"
    assert mod.os.environ["CRUSOE_MODEL"] == "filemodel"


def test_classify():
    mod = _load()
    ok = {"tool_calls": [{"function": {"name": "get_weather", "arguments": '{"city":"Paris"}'}}]}
    weak = {"tool_calls": [{"function": {"name": "get_weather", "arguments": "not json"}}]}
    fail = {"content": "hello"}
    assert mod._classify(ok) == ("PASS", "")
    assert mod._classify(weak)[0] == "WEAK"
    assert mod._classify(fail)[0] == "FAIL"
    for arguments in ('{"city": null}', '{"city": 123}', '{"city": []}', '{"city": ""}'):
        bad = {"tool_calls": [{"function": {"name": "get_weather", "arguments": arguments}}]}
        assert mod._classify(bad)[0] == "WEAK"
    paris = {"tool_calls": [{"function": {"name": "get_weather", "arguments": '{"city": "Paris"}'}}]}
    assert mod._classify(paris) == ("PASS", "")


def test_recommend():
    mod = _load()
    models = [
        {"id": "moonshotai/Kimi-K2.6", "context_length": 262144},
        {"id": "zai/GLM-5.2", "context_length": 128000},
        {"id": "nvidia/Nemotron-3-Nano", "context_length": 131072},
        {"id": "qwen/Qwen3-8B", "context_length": 8192},
    ]
    results = [
        {"model": "zai/GLM-5.2", "result": "PASS", "latency_ms": 10},
        {"model": "nvidia/Nemotron-3-Nano", "result": "PASS", "latency_ms": 40},
        {"model": "moonshotai/Kimi-K2.6", "result": "PASS", "latency_ms": 90},
        {"model": "qwen/Qwen3-8B", "result": "FAIL", "latency_ms": 5},
    ]
    rec = mod.recommend(results, models)
    assert rec["fast"] == "zai/GLM-5.2"
    assert rec["strong"] == "moonshotai/Kimi-K2.6"
    assert rec["critic"] == "zai/GLM-5.2"
    assert rec["note"] == "3 PASS"
    one = mod.recommend(
        [{"model": "qwen/Qwen3-8B", "result": "PASS", "latency_ms": 1}], models
    )
    assert "fewer than 3" in one["note"]
    assert one["critic"] is None


def test_mock_json_end_to_end(capsys, monkeypatch):
    mod = _load()
    monkeypatch.delenv("CRUSOE_API_KEY", raising=False)
    rc = mod.main(["--mock", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert {"models", "results", "recommendation"} <= payload.keys()
    assert payload["recommendation"]["critic"] == "zai/GLM-5.2"


def test_missing_key_exit_2(tmp_path, monkeypatch, capsys):
    mod = _load()
    monkeypatch.delenv("CRUSOE_API_KEY", raising=False)
    _point_env_root(mod, monkeypatch, tmp_path)
    assert mod.main([]) == 2
    capsys.readouterr()
