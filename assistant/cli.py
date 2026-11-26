"""Command line: `uv run python -m assistant review <pack folder>`.

Implements: assistant/runs-offline, assistant/cost-first, assistant/human-approves

`review` drafts: offline by default (it replays the recorded model reply); `--live` calls OpenRouter instead, after
printing the estimated cost, and only with `--yes`. It writes the draft to a file and releases nothing.
`release <draft> --analyst NAME` is the human gate, run after the analyst has read, edited and ticked the draft.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from assistant import llm, report, rules


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="assistant", description="Draft a KYC review from a client's document pack.")
    sub = ap.add_subparsers(dest="command", required=True)
    rv = sub.add_parser("review", help="read a pack and print the analyst's draft")
    rv.add_argument("pack", type=Path)
    rv.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    rv.add_argument("--live", action="store_true", help="call a model on OpenRouter instead of the recorded reply")
    rv.add_argument("--model", default=llm.DEFAULT_MODEL)
    rv.add_argument("--yes", action="store_true", help="accept the printed cost estimate for a live call")
    rv.add_argument("--record", action="store_true", help="save the live reply as this pack's replay")
    rv.add_argument("--drafts", type=Path, default=Path("scratch/drafts"), help="where the draft is written")
    rl = sub.add_parser("release", help="release an approved draft (after the analyst ticked it)")
    rl.add_argument("draft", type=Path)
    rl.add_argument("--analyst", required=True)
    rl.add_argument("--outbox", type=Path, default=Path("scratch/outbox"))
    args = ap.parse_args(argv)

    if args.command == "release":
        try:
            print(f"Released by {args.analyst}: {report.release(args.draft, args.analyst, args.outbox)}")
            return 0
        except PermissionError as e:
            print(f"Not released: {e}")
            return 1

    note = ""
    if args.live:
        key = llm.key()
        if not key:
            print("No OPENROUTER_API_KEY in the environment. Put it in .env and run with `uv run --env-file .env`.")
            return 2
        prompt = llm.build_prompt(args.pack)
        tokens, cost = llm.estimate(prompt, args.model)
        print(f"Estimated cost: about {tokens} input tokens on {args.model}, ${cost:.4f} for one call.")
        if not args.yes:
            print("Not calling the model. Run again with --yes to accept this cost.")
            return 2
        extraction = llm.call(prompt, args.model, key)
        if extraction is None:
            print(f"{args.model} didn't reply with JSON, so there is nothing to check. Nothing recorded.")
            return 1
        note = f"live reply from {args.model}"
        if args.record:
            print(f"Recorded to {llm.record(args.pack, extraction, args.model)}")
    else:
        extraction = llm.replay(args.pack)
        note = llm.replay_note(args.pack)

    result = rules.evaluate(args.pack, extraction, args.as_of)
    text = report.markdown(result, note)
    print(text)
    print(f"Draft written to {report.write_draft(result, text, args.drafts)}. Nothing has been released.")
    return 0
