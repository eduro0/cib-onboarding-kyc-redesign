<!-- Implements: assistant/live-scored -->
# KYC review assistant (prototype)

Serves one step of the To-Be map: reading a corporate client's KYC pack and drafting the analyst's review. The model
only reads. It extracts facts, each with the exact words it came from. Fixed rules in `rules.py` do the deciding:
beneficial owners, what is missing, what changed, and the one consolidated client request. A fact counts only if
its quote is in the named document and contains the claimed value; document types and dates are read from each
document's header by rules. `review` writes a draft and releases nothing; `release` is a separate step that sends
exactly the text the analyst ticked and possibly edited. All samples are fictional.

```sh
uv run python -m assistant review assistant/samples/harbour-lantern            # onboarding, offline replay
uv run python -m assistant review assistant/samples/kestrel-bay                # review with changes
uv run python -m assistant review assistant/samples/quiet-pine                 # review, nothing changed
# the analyst reads the draft file, edits it if needed, ticks a box, then:
uv run python -m assistant release scratch/drafts/<draft>.md --analyst "A. Analyst"
```

The default run replays `replays/<pack>.json`: a reply written by hand to the prompt's schema, so the demo needs no
key. A live run on OpenRouter needs `OPENROUTER_API_KEY` in `.env`. It prints the estimated cost first and does
nothing without `--yes`. The default model is a free one.

```sh
uv run --env-file .env python -m assistant review assistant/samples/harbour-lantern --live          # prints the estimate, stops
uv run --env-file .env python -m assistant review assistant/samples/harbour-lantern --live --yes --record
```

A live reply is checked like any other: a fact whose quote isn't in the named document is dropped and flagged.

**Live runs.** Every sample pack has been run on real models. `scripts/live_run.py` makes the calls and records them
in `live/`, apart from the hand-written replies, which stay the offline demo and the answer key. `make build` scores
each reply against the hand-written one (`scripts/score_live.py`, full table in [`live/results.md`](live/results.md)).
Over the <!-- check: live.claude-sonnet-5-5.packs = 3 -->3 packs, the hand-written replies hold
<!-- check: live.claude-sonnet-5-5.key_facts = 32 -->32 verified facts:

- the free default, `nvidia/nemotron-3-ultra-550b-a55b:free`, produced
  <!-- check: live.nemotron-3-ultra-550b-a55b-free.found = 31 -->31 of them, with
  <!-- check: live.nemotron-3-ultra-550b-a55b-free.dropped = 0 -->0 dropped by verification, and led to the same
  flags on <!-- check: live.nemotron-3-ultra-550b-a55b-free.flags_same = 2 -->2 packs and the same client request
  on <!-- check: live.nemotron-3-ultra-550b-a55b-free.request_same = 2 -->2. On the other it wrote a shareholder as
  "Northgate Ventures Ltd (British Virgin Islands)", as its quote does, so the same flags name it that way;
- `anthropic/claude-sonnet-5.5` produced <!-- check: live.claude-sonnet-5-5.found = 29 -->29 of them, with
  <!-- check: live.claude-sonnet-5-5.dropped = 0 -->0 dropped, and led to the same flags on
  <!-- check: live.claude-sonnet-5-5.flags_same = 3 -->3 packs and the same client request on
  <!-- check: live.claude-sonnet-5-5.request_same = 3 -->3, for
  $<!-- check: live.claude-sonnet-5-5.cost_usd = 0.0686 -->0.0686 in all. All
  <!-- check: live.claude-sonnet-5-5.missed_entity = 3 -->3 of its
  <!-- check: live.claude-sonnet-5-5.missed = 3 -->3 misses were entity fields it left out, such as the registered
  address.

The rules don't flag a missing registered address or jurisdiction, so an analyst reading the draft has to notice
it. The first free default, `google/gemma-4-31b-it:free`, was rate-limited upstream throughout the run, so it
was replaced.

```sh
uv run --env-file .env python scripts/live_run.py          # prints the estimate for every pack and model, stops
uv run --env-file .env python scripts/live_run.py --yes    # calls, records to live/, then: make build
```
`prompts/extract.md` is the exact text the model reads. The demo packs are plain-text documents with a header
line (`DOCUMENT: ...`); real scanned documents would need a classification step the analyst confirms.

**What it doesn't do.** It finds beneficial owners by multiplying shareholdings along each chain. Where a person
holds a majority of a company in the chain it raises a CONTROL_CHECK flag rather than deciding control itself. AMLO also counts a person who
"exercises ultimate control over the management" [src:hk-amlo-sch2], and that needs an analyst's judgment. It
doesn't screen names (the To-Be map gives screening its own step), rate risk, or handle trusts, partnerships or
bearer shares. The samples are three small fictional packs, so they show the design, not its accuracy.

| File | Does |
|---|---|
| `llm.py` | prompt, replay, cost estimate, the OpenRouter call |
| `rules.py` | quote verification, ownership chains, document rules, review changes, the client request |
| `requirements.yaml` | the document rules and thresholds, with their basis |
| `report.py` | the analyst's draft, and the approval gate |
| `cli.py` | the command line |
