"""The model half of the assistant: it only reads documents and returns extracted facts.

Implements: assistant/runs-offline, assistant/cost-first, assistant/llm-reads-rules-decide, assistant/live-scored

`replay()` returns a recorded reply for a sample pack, so the demo needs no key and no network. `call()` sends the
verbatim prompt in `prompts/extract.md` plus the pack to OpenRouter. The CLI prices a live call with
`estimate()` first and refuses to make it without `--yes`. `record()` saves a live reply as the pack's new replay;
`scripts/live_run.py` uses `call_full()` to keep live replies apart, in `assistant/live/`, with what each call cost.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPT = ROOT / "prompts" / "extract.md"
REPLAYS = Path(__file__).parent / "replays"
DEFAULT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"  # Gemma 4 free was rate-limited upstream on 2026-11-25
API = "https://openrouter.ai/api/v1"
EXPECTED_OUTPUT_TOKENS = 2500


def build_prompt(folder: Path) -> str:
    parts = [PROMPT.read_text(encoding="utf-8")]
    for path in sorted(Path(folder).glob("*.txt")):
        parts.append(f"=== FILE: {path.name} ===\n{path.read_text(encoding='utf-8')}")
    return "\n\n".join(parts)


def replay(folder: Path) -> dict:
    return json.loads((REPLAYS / f"{Path(folder).name}.json").read_text(encoding="utf-8"))["reply"]


def replay_note(folder: Path) -> str:
    return json.loads((REPLAYS / f"{Path(folder).name}.json").read_text(encoding="utf-8"))["fixture"]


def price_per_token(model: str) -> tuple[float, float]:
    """(prompt, completion) USD per token, from OpenRouter's public model list (no key needed)."""
    with urllib.request.urlopen(f"{API}/models", timeout=20) as r:
        for m in json.load(r)["data"]:
            if m["id"] == model:
                return float(m["pricing"]["prompt"]), float(m["pricing"]["completion"])
    raise ValueError(f"unknown OpenRouter model: {model}")


def estimate(prompt: str, model: str) -> tuple[int, float]:
    """Rough input tokens (4 characters each) and the cost in USD of one call."""
    tokens = len(prompt) // 4
    p_in, p_out = price_per_token(model)
    return tokens, tokens * p_in + EXPECTED_OUTPUT_TOKENS * p_out


def call(prompt: str, model: str, key: str) -> dict:
    return call_full(prompt, model, key)[0]


def call_full(prompt: str, model: str, key: str) -> tuple[dict | None, dict]:
    """The parsed reply (None if it isn't JSON) and what the call used: tokens, cost in USD, the raw text."""
    body = json.dumps({"model": model, "temperature": 0, "response_format": {"type": "json_object"},
                       "usage": {"include": True}, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(f"{API}/chat/completions", data=body, method="POST",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for attempt in range(6):  # free models share an upstream pool that often answers 429: wait and retry
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                answer = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code not in (429, 502, 503) or attempt == 5:
                raise
            time.sleep(15 * (attempt + 1))
    raw = answer["choices"][0]["message"]["content"] or ""
    usage = answer.get("usage") or {}
    used = {"prompt_tokens": usage.get("prompt_tokens", 0), "completion_tokens": usage.get("completion_tokens", 0),
            "cost_usd": usage.get("cost", 0.0), "raw": raw}
    content = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(content), used
    except json.JSONDecodeError:
        return None, used


def key() -> str | None:
    return os.environ.get("OPENROUTER_API_KEY")


def record(folder: Path, reply: dict, model: str) -> Path:
    path = REPLAYS / f"{Path(folder).name}.json"
    path.write_text(json.dumps({"fixture": f"Recorded from a live call to {model} on OpenRouter.", "reply": reply},
                               indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
