---
name: deliver
description: Deliver one work item from ready to merged - spec, failing check, build, trace, try it, fresh review, merge, log. Use when asked to do, build or ship a work item, or to run the whole queue ("one-shot").
---

<!-- Implements: workflow/item-first, workflow/spec-first, workflow/check-first, workflow/blocked-means-ask, workflow/try-it, workflow/fresh-review, workflow/measured, workflow/pace -->

# Deliver a work item

**Pace:** build the smallest thing that meets the item's boxes. Fix real problems; decline speculative hardening and
edge cases nobody has hit, and say why.

## 1. Start

1. Pick the lowest-numbered item with `status: ready` whose `Blocked by` items are all `done`. Set it to
   `status: in-progress` and note the start time under "Log". Read the time from the clock (`date +%H:%M`) or a
   commit timestamp, never from memory.
2. `git switch -c NNN-slug main`. If a reviewer or another item is running at the same time, use a worktree
   instead, one per item, so nobody's checkout changes under them:
   `git worktree add <scratchpad>/wt-NNN -b NNN-slug main`. Copy any `*.local.txt` files into it.

## 2. Spec

Add or change the statements this item touches in `spec/product/` (see `interview` step 3 for the format). Commit:
`Spec: <what>`. If the item doesn't say what the owner wants, follow "Blocked" below.

## 3. Failing check

Write the check or test that proves each new statement: a test in `tests/`, or a check in `checks/project/`. Run it
and see it **fail for the right reason** (a missing file counts). Ask of each test: would it fail if the rule
broke? Once, break the thing on purpose and watch it fail; a test that reads its answer from the thing it checks
can't fail. Commit: `Check: <what>`. Never edit an existing
check to make it pass; a check that is wrong gets fixed in its own `Check:` commit with the reason in the body.

## 4. Build

Produce the smallest thing that passes. Generated artifacts come from a committed script run by `make build`, never
by hand, so they can be remade. Make them byte-reproducible (fixed dates inside Office files and zips), so a test
can tell a stale file from a fresh one. Commit in small steps: `Build: <what>`.

## 5. Trace

Fill in each statement's row in "Where this is enforced": the files that enforce it and the checks that prove it.
Each text file you name carries an `Implements: area/statement` comment. Run `make check` until it is green.

## 6. Try it for real

Open, render or run the result the way its user would: render the diagram to PNG and look at it, open the
spreadsheet, run the assistant on a sample. Put anything you make for this in the scratchpad, not the repository.
- On a diagram, follow every branch from start to end. A glance misses a line drawn through the wrong box.
- On a slide or page, look at it at the size it will be shown. Text that's fine in the file can be unreadable
  on the slide.
- On numbers, compare them with an outside anchor (a published benchmark, a sanity bound). Implausible results
  discredit everything around them.
Write what you saw in one line under "Log".

## 7. Review

Start a **fresh** subagent with the `review` skill. Give it the item path and `git diff main...HEAD`, and nothing
about how you built it. Then, for each finding:
- P1 (wrong, broken, contradicts the spec, breaks a hard rule): fix it in a new commit, all P1s in one go;
- anything else: answer "follow-up: <reason>" and open a new item only if it's a real problem.

One round. Write the counts under "Log": found / fixed / declined.

## 8. Merge and log

1. Tick the boxes that are met. A box you can't tick goes under "Questions" with the reason.
2. Set `status: done`, then commit.
3. `git switch main && git merge --no-ff NNN-slug -m "Merge NNN-slug: <outcome>"`. Run `make check` on `main`. If it's
   red, fix that before anything else merges.
4. Add a row to `METRICS.md`. If an agent made a mistake on the way, add it to `LESSONS.md`.

## Blocked

Write the question and your recommended answer under "Questions" on the item, mark the decision
`(default, owner to confirm)` in the spec, and carry on with that answer. Stop only if every way forward needs the
owner: spending, an account, a key or publishing. In that case, set `status: blocked` and move to the next item.

## One-shot mode

When asked to run the queue: loop over steps 1 to 8 until no item is `ready`. Then report in under 20 lines: what
merged, what's blocked and on what, every default you chose, and the full "Owner does" list.
