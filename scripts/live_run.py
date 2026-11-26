"""Run every sample pack on real models through OpenRouter and record the replies in `assistant/live/`.

Implements: assistant/live-scored, assistant/cost-first

    uv run --env-file .env python scripts/live_run.py                 # prints the estimate, calls nothing
    uv run --env-file .env python scripts/live_run.py --yes           # calls, records, then run `make build`

The hand-written replies in `assistant/replays/` stay untouched: they are the offline demo and the answer key that
`scripts/score_live.py` scores these recordings against.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from assistant import llm  # noqa: E402

SAMPLES = ROOT / "assistant" / "samples"
LIVE = ROOT / "assistant" / "live"
MODELS = [llm.DEFAULT_MODEL, "anthropic/claude-sonnet-5.5"]


def slug(model: str) -> str:
    return model.replace("/", "__").replace(":", "_")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--models", nargs="+", default=MODELS)
    ap.add_argument("--packs", nargs="+", default=sorted(p.name for p in SAMPLES.iterdir() if p.is_dir()))
    ap.add_argument("--yes", action="store_true", help="accept the printed cost estimate")
    args = ap.parse_args(argv)
    key = llm.key()
    if not key:
        print("No OPENROUTER_API_KEY in the environment. Put it in .env and run with `uv run --env-file .env`.")
        return 2
    total = 0.0
    for model in args.models:
        for pack in args.packs:
            tokens, cost = llm.estimate(llm.build_prompt(SAMPLES / pack), model)
            total += cost
            print(f"{model:40} {pack:16} ~{tokens} input tokens, ${cost:.4f}")
    print(f"Estimated total: ${total:.4f} for {len(args.models) * len(args.packs)} calls.")
    if not args.yes:
        print("Not calling any model. Run again with --yes to accept this cost.")
        return 2
    spent = 0.0
    for model in args.models:
        for pack in args.packs:
            reply, used = llm.call_full(llm.build_prompt(SAMPLES / pack), model, key)
            spent += used["cost_usd"]
            out = LIVE / pack / f"{slug(model)}.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            record = {"model": model, "date": date.today().isoformat(), "prompt_tokens": used["prompt_tokens"],
                      "completion_tokens": used["completion_tokens"], "cost_usd": used["cost_usd"], "reply": reply}
            if reply is None:
                record["raw"] = used["raw"]
            out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"{model:40} {pack:16} {'ok' if reply is not None else 'NOT JSON'}, ${used['cost_usd']:.4f} -> {out.relative_to(ROOT)}")
    print(f"Spent ${spent:.4f} as reported by OpenRouter. Now run `make build` to score the replies.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
