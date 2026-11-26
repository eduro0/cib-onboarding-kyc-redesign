"""Tests for the live runs: recorded replies from real models, scored against the hand-written ones.

Implements: assistant/live-scored
"""

import copy
import json
from pathlib import Path

from assistant import llm
from scripts import score_live

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "assistant" / "samples"
LIVE = ROOT / "assistant" / "live"
FIELDS = {"model", "date", "prompt_tokens", "completion_tokens", "cost_usd", "reply"}


def test_live_scored_every_pack_has_a_free_and_a_paid_recording():
    for pack in sorted(p for p in SAMPLES.iterdir() if p.is_dir()):
        runs = [json.loads(f.read_text()) for f in sorted((LIVE / pack.name).glob("*.json"))]
        assert any(r["model"].endswith(":free") for r in runs), f"{pack.name}: no free-model recording"
        assert any(not r["model"].endswith(":free") for r in runs), f"{pack.name}: no paid-model recording"
        for r in runs:
            assert FIELDS <= r.keys(), f"{pack.name}: a recording lacks {FIELDS - r.keys()}"
            assert r["prompt_tokens"] > 0 and r["completion_tokens"] > 0


def test_live_scored_a_perfect_reply_scores_perfect_and_a_missing_fact_is_caught():
    folder = SAMPLES / "harbour-lantern"
    key = llm.replay(folder)
    same = score_live.score(folder, key)
    assert same["missed"] == 0 and same["dropped"] == 0 and same["flags_same"] and same["request_same"]
    worse = copy.deepcopy(key)
    worse["director_mentions"] = [m for m in worse["director_mentions"] if "LIM" not in m["name"]]
    lost = score_live.score(folder, worse)
    assert lost["missed"] == 1 and not lost["flags_same"]


def test_live_scored_results_file_is_fresh():
    assert (LIVE / "results.md").read_text(encoding="utf-8") == score_live.render(), "run `make build`"


def test_live_scored_readme_traces_its_numbers():
    text = (ROOT / "assistant" / "README.md").read_text(encoding="utf-8")
    assert "<!-- check: live." in text and "live/results.md" in text


def test_live_scored_numbers_are_fresh():
    numbers = json.loads((ROOT / "build" / "numbers.json").read_text(encoding="utf-8"))
    assert {k: v for k, v in numbers.items() if k.startswith("live.")} == score_live.numbers(), "run `make build`"


def test_live_scored_the_free_default_has_been_run_on_every_pack():
    for pack in sorted(p for p in SAMPLES.iterdir() if p.is_dir()):
        models = {json.loads(f.read_text())["model"] for f in (LIVE / pack.name).glob("*.json")}
        assert llm.DEFAULT_MODEL in models, f"{pack.name}: the default model {llm.DEFAULT_MODEL} hasn't been run"


def test_live_scored_every_readme_number_is_traced():
    text = (ROOT / "assistant" / "README.md").read_text(encoding="utf-8")
    para = text[text.index("**Live runs.**"):text.index("```sh", text.index("**Live runs.**"))]
    import re
    bare = re.sub(r"<!--.*?-->\S*", "", para)  # drop each marker and the value it traces
    bare = re.sub(r"`[^`]*`|\[[^\]]*\]\([^)]*\)|\d{4}-\d{2}-\d{2}", "", bare)  # model ids, links, dates
    assert not re.search(r"\d", bare), f"an untraced number in the live-runs paragraph: {re.findall(r'.{20}\\d.{20}', bare)}"


def test_live_scored_a_reply_that_is_not_json_is_never_recorded_over_the_answer_key(monkeypatch, tmp_path):
    from assistant import cli
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    monkeypatch.setattr(llm, "price_per_token", lambda model: (0.0, 0.0))
    monkeypatch.setattr(llm, "call", lambda *a, **k: None)
    recorded = []
    monkeypatch.setattr(llm, "record", lambda *a, **k: recorded.append(a))
    code = cli.main(["review", str(SAMPLES / "quiet-pine"), "--live", "--yes", "--record", "--drafts", str(tmp_path)])
    assert code != 0 and not recorded
