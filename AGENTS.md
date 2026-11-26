<!-- Implements: workflow/entry-point, workflow/owner-only, workflow/pace, workflow/no-weakening, workflow/blocked-means-ask, workflow/numbers-traced, workflow/trivial-path -->
# CIB onboarding & KYC redesign: agent guide

A public portfolio piece on AI in bank operations: As-Is and To-Be maps of corporate client onboarding and KYC periodic review, a simulated KPI model, an AI assistant with human approval gates, and a rollout and change-risk plan.

## Where things are

- **Spec (intent, read first):** `spec/product/` (what we deliver) and `spec/contributing/` (how we work). One file
  per area, one rule per line. Each file ends with "Where this is enforced", which names the file that enforces each
  rule and the check that proves it.
- **Work:** one file per item in `work/` (`NNN-slug.md`), with a status line. `work/README.md` explains the format.
- **Sources:** `sources/` holds every outside fact we rely on, with its URL, an exact quote and the date accessed.
- **Checks:** `make check` runs `checks/check.py` plus the project checks in `checks/project/`. The Stop hook runs it
  before you finish.
- **Skills:** `.agents/skills/` (also linked as `.claude/skills/`): `interview` (brief to spec and work items),
  `deliver` (one work item, start to merged), `review` (fresh-context review), `debrief` (lessons to fixes).

## Hard rules

- The owner handles accounts, API keys, spending and anything published outside this folder. Write the exact steps
  under "Owner does" in the work item. Never put keys in files, logs or commits.
- Every number comes from a committed script (marked `<!-- check: key = value -->`) or from `sources/`. Never from
  memory.
- Never weaken a check or a test to make it pass. If a check is wrong, fix it in its own commit and say why.
- Blocked or unsure? Write the question and your recommended answer under "Questions" in the work item, go with that
  answer, and carry on.

## Pace

Build the smallest thing that meets the item's acceptance boxes. Fix real problems; decline speculative hardening and
edge cases nobody has hit, with a reason. One review round per item.

## Commands

```sh
make check    # every check; must pass before an item is done
make test     # the tests behind the checks
make build    # regenerate every generated artifact
```

## The loop

Every work item goes **spec → failing check → build → trace → try it → review → merge → log** (`deliver`).
Trivial fixes (a typo, one line) skip the loop with a `Trivial:` commit on `main`.
