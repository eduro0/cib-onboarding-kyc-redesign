# CIB onboarding & KYC redesign

An AI-first redesign of two banking processes, built as a public portfolio piece: corporate client onboarding,
and the periodic review that keeps a client's file current. It maps both processes as they work today, redesigns
them so AI reads and drafts while people decide, estimates the gain on simulated cases, builds the AI step as a
working prototype, and plans the rollout and its risks.

**Not affiliated with or endorsed by BBVA or any other bank.** The piece was made with BBVA's AI Processes role
for corporate and investment banking (CIB) in Asia in mind, but it describes an illustrative CIB branch in Hong
Kong, not any real bank's processes. It uses only public material. Every KPI figure is simulated, and every
company and person in the examples is fictional.

- **Published site:** <https://sites.google.com/view/ai-cib-onboarding-kyc>
- **Access guide** (every published file, what it holds and where its data comes from):
  <https://docs.google.com/document/d/13qo1W_dyERFWfOc8_hp9xxHEUo45bj3leV33IhyhCZk/edit>

## What it is and why

Opening an account for a company is slow because the bank must establish who really owns and controls it. This
check is called KYC, "know your customer". A corporate client sends a pack of documents (certificate of
incorporation, register of directors, shareholder lists, identity documents), an analyst reads them, and every
gap means another request to the client. The same work comes back at each periodic review. Analyst time and
repeated client requests are the two costs this project goes after. The rules followed are Hong Kong's
[src:hk-amlo-sch2] [src:hkma-aml-cft-guideline-2023], with Singapore's noted where they differ
[src:mas-notice-626]. Each `[src:...]` tag names an entry in `sources/`, which holds the public page, the exact
quote relied on and the date it was read.

The project has five parts, each a file you can open:

1. **As-Is and To-Be process maps.** A process map shows each step, who does it and where the work goes next.
   Both maps are in BPMN 2.0, the standard notation for business processes, and open in
   [bpmn.io](https://demo.bpmn.io). The As-Is map (today) marks each pain point and its cause. The To-Be map (the
   redesign) draws every AI step as its own task. Every AI output that could change a client's status, risk
   rating or file passes a named human approval step, called a gate, before it takes effect. Both maps mark the
   same "moments of truth", the points where the client forms an opinion of the bank. Files:
   `deliverables/maps/`.
2. **A KPI model.** A KPI (key performance indicator) is a figure used to judge the process: here, days from
   first request to account live, staff hours per case, the share of cases done without rework, and how many
   separate requests reach the client. A script walks a simulated year of cases through both maps with a fixed
   random seed, so the figures can be remade exactly. In the simulation the average onboarding takes
   <!-- check: onb_cycle_days_as_is = 63.6 -->63.6 days today and
   <!-- check: onb_cycle_days_to_be = 36.1 -->36.1 days after the redesign (simulated). Every input is a labelled
   guess with its reason, so a reader can argue with any of them. Files: `deliverables/kpi-model.xlsx` (imports
   into Google Sheets), `docs/assumptions.md`.
3. **An AI assistant with human approval gates.** A prototype of the redesigned document-review step. A language
   model only extracts facts, each with the exact words it came from. Fixed rules then decide who the beneficial
   owners are, what is missing, what changed and what to ask the client, in one consolidated request. Nothing is
   released until an analyst ticks an approval box and names themselves. Files: `assistant/`.
4. **A rollout roadmap and a change-risk register.** The roadmap phases the rollout and names, for each phase,
   who has to agree and the KPI that decides whether the next phase starts. The register lists risks to staff,
   clients, controls and regulators, each with its likelihood, impact, mitigation, owner and warning signal.
   Files: `docs/roadmap.md`, `docs/change-risks.md`.
5. **A slide deck and Google-tool packs** that tell the story and rebuild it on free Google tools (Slides, Docs,
   Sheets, Data Studio, Sites, a Gemini Gem, Gemini Notebook). Files: `deliverables/deck.pptx`, `docs/`,
   `deliverables/gem/`.

## Repository layout

| Folder | Holds |
|---|---|
| `model/` | the two process maps as readable YAML, and the simulation's assumptions with their reasons |
| `scripts/` | the generators: simulation, maps, workbook, charts, deck, Word exports, live-run scoring |
| `assistant/` | the KYC review prototype, its fictional sample packs, recorded model replies and live-run scores |
| `prompts/` | the exact text the assistant's model reads |
| `docs/` | the roadmap, change risks, assumptions and access guide (exported to Word), plus the Google-tool guides |
| `deliverables/` | generated outputs: maps, workbook, charts, deck, Word documents, the Gem pack |
| `build/` | generated intermediates, including `numbers.json`, the single list of figures that text may quote |
| `sources/` | every outside fact relied on, with URL, exact quote and date accessed |
| `spec/` | what the project must deliver and how it is built, one rule per line, each tied to the check that proves it |
| `checks/`, `tests/` | the checks behind `make check` and the tests behind them |
| `work/` | the format for work items (the original build's items are not included) |

## Install and run

You need Python 3.11 or later and [uv](https://docs.astral.sh/uv/), a Python package manager. Everything below
runs offline with no account or API key.

```sh
uv sync       # install the dependencies into .venv
make test     # run the test suite
make check    # every check, then the tests; this is the bar for any change
make build    # regenerate every generated file from the model files
```

`make check` fails if any figure in the text differs from the model's output, if a passage that names a regulator
cites no recorded source, if a public page showing a KPI does not say it is simulated, or if anything looks like
an API key. A figure in the text is tied to the model by a hidden marker such as
`<!-- check: onb_cycle_days_as_is = 63.6 -->`, which the check compares with `build/numbers.json`. `make build` is
reproducible: on a clean checkout it should leave `git status` unchanged.

### The assistant demo

The demo replays a model reply written by hand, so it needs no key or network:

```sh
uv run python -m assistant review assistant/samples/harbour-lantern   # new client onboarding
uv run python -m assistant review assistant/samples/kestrel-bay       # periodic review with changes
uv run python -m assistant review assistant/samples/quiet-pine        # periodic review, nothing changed
```

`review` prints the analyst's draft and saves it under `scratch/drafts/`. It releases nothing. To release, open the
draft, edit the client request if needed, tick one box under "Analyst decision", then run:

```sh
uv run python -m assistant release scratch/drafts/<draft>.md --analyst "A. Analyst"
```

Release refuses a draft with no ticked box or no analyst name, refuses a rejected draft, and sends exactly the
text the analyst left. The released message is written to `scratch/outbox/`. `assistant/README.md` explains the
design and what the assistant does not do.

### Live model runs (API key needed)

Only the live runs call a real model. They use [OpenRouter](https://openrouter.ai), a service that routes one API
to many models. To try one, copy `.env.example` to `.env` and set `OPENROUTER_API_KEY`. The `.env` file is
git-ignored.

```sh
uv run --env-file .env python -m assistant review assistant/samples/harbour-lantern --live        # prints the cost estimate, stops
uv run --env-file .env python -m assistant review assistant/samples/harbour-lantern --live --yes  # makes the call
uv run --env-file .env python scripts/live_run.py --yes   # rerun every pack on every model, then: make build
```

A live run prints its estimated cost first and does nothing without `--yes`; the default model is a free one.
Each sample pack has already been run on a free and a paid model. Those replies are committed in
`assistant/live/` and scored against the hand-written replies in `assistant/live/results.md`, so the checks and
the build need no key.

## How it was built

The project was built by AI coding agents working to a written specification, with a person deciding scope and
handling anything that needed an account. `AGENTS.md` is the agents' entry point. Each piece of work followed the
same loop: write the rule in `spec/`, write a check that fails without it, build until the check passes, run the
result for real, then have a separate agent that did not build it review it against the spec. While `make check`
fails, a Claude Code hook stops an agent from finishing, and a git hook in `.githooks/` refuses the commit (turn
it on with `git config core.hooksPath .githooks`). The loop's steps are written up as
skills in `.agents/skills/` (`interview`, `deliver`, `review`, `debrief`).

The method's main safeguard is that numbers and claims are checked mechanically rather than trusted. A figure
must come from the model's output and a claim about the rules must cite a recorded source, so a reader can trace
any statement to its origin.

## License

MIT. See [LICENSE](LICENSE).
