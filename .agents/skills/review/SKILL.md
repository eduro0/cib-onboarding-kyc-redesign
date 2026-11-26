---
name: review
description: Review one work item's branch with fresh eyes - spec first, then checks, then the result - and report only correctness problems. Use as a subagent that did not build the item.
---

<!-- Implements: workflow/fresh-review, workflow/spec-first, workflow/no-weakening, workflow/numbers-traced -->

# Review a work item

You did not build this, and you shouldn't trust that it works. You get the item file and the diff. Read in this
order and report problems:

1. **Spec.** Does each new or changed statement say what we want, not how, in one plain sentence that contradicts
   nothing? A change in what we deliver with no spec change, where the spec doesn't already cover it, is a finding.
2. **Checks.** Do the checks named in "Where this is enforced" actually prove the statements? For each test ask:
   would it fail if the rule broke? A test that asserts once per file what the rule says per item, or reads its
   answer from the thing it checks, proves nothing. **Read every change to an existing check or test on its
   own**: a check that was loosened, deleted, exempted or made to skip is a P1, and so is one changed inside a
   `Build:` commit.
3. **Result.** Does the artifact do what the statements and the acceptance boxes say? Open or run it if you can.
4. **Numbers and facts.** Every number either carries a `check:` marker or cites a key in `sources/`, and every claim
   about the outside world cites a source. A number from nowhere is a P1. Then read the quote behind each
   citation: does it say what the sentence claims? A citation that exists but doesn't support its sentence is a
   P1. The same goes for any extraction: a quote that exists isn't proof that it contains the claimed value.
5. **Hard rules.** No keys or secrets. No banned terms (`make check` catches the listed ones; also look for anything
   that reads as confidential). Nothing published.

**Don't report** style, wording preferences, speculative hardening, edge cases nobody will hit, or anything
`make check` already checks. A reviewer asked for problems always finds something; report only what is wrong.

**Output:** a list. Each line says `P1` or `P2`, the `file:line`, what's wrong and what would fix it. If nothing is
wrong, say "No findings." That's a good outcome, not a failure.
