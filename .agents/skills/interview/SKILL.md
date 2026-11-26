---
name: interview
description: Turn a brief, a rambling voice note or a conversation into spec statements and a queue of work items. Use at the start of a project, or when the owner describes something new they want.
---

<!-- Implements: workflow/item-first, workflow/spec-first, workflow/blocked-means-ask -->

# Interview: brief to spec to work items

The owner talks loosely, often by `/voice`. Your job is to turn that into intent the rest of the work can rely on.
They should never have to brief anyone twice.

1. **Read** the brief and anything it points to. List the facts it fixes, the choices it leaves open, and the
   constraints (money, deadline, confidentiality, tools).
2. **Ask only what changes the plan.** Put up to four questions in one message, each with your recommended answer.
   In one-shot mode, don't ask: take your recommendation and mark it `(default, owner to confirm)`.
3. **Write the product spec**, one file per area in `spec/product/`:
   - one statement per line, `- **name:** one plain sentence of what we want and why`, never how;
   - names are lowercase words joined by hyphens and unique in the file;
   - mark each statement `(decided)` when the owner or the brief settled it, `(default, owner to confirm)` when you
     chose it, `(guess)` for a predicted number written down so it can be argued with;
   - end the file with `## Where this is enforced` and one row per statement, with `not yet` until it's built.
4. **Cut the work into items** in `work/`, using `work/_template.md`:
   - one deliverable per item, and boxes each checkable by looking at the result;
   - order them with `Blocked by:` lines;
   - anything only the owner can do (accounts, keys, spending, publishing) goes under "Owner does", step by step.
5. Run `make check` and fix what it reports.
6. **Report** in under 15 lines: the areas, the items in order, the defaults you chose, and the owner's to-do list.
