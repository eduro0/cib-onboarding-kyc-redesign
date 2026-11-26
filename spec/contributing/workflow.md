# Workflow

- **entry-point:** Agents start from `AGENTS.md`, which sends them to the spec, the work items and the skills, so nobody is briefed twice.
- **owner-only:** Only the owner deals with accounts, keys, spending and publishing, so an agent can never cost money or make something public by mistake.
- **pace:** Each item aims for the smallest result that meets its acceptance boxes, so effort goes into what was asked.
- **item-first:** Every piece of work that isn't trivial starts from a well-formed work item, so its outcome and its finish line are written down before work starts.
- **spec-first:** A change in what we deliver starts with a change to its statements in `spec/product/`.
- **check-first:** The check that proves a statement is written and seen failing before the work that makes it pass.
- **no-weakening:** Checks and tests are never loosened to make work pass; a wrong check is fixed in its own commit with a reason.
- **blocked-means-ask:** A blocked agent records its question with a recommended answer on the item, proceeds on that answer and keeps going.
- **checked-before-done:** An agent can't finish, or commit anything but a `Check:` commit, while `make check` fails, so broken work is caught before anyone looks at it.
- **try-it:** Before review, the result is opened, rendered or run for real, because passing checks are not proof it works.
- **fresh-review:** Every item gets one review round by an agent that did not build it, on correctness against the spec only.
- **numbers-traced:** Every number we publish comes from a committed script or a recorded source, never from memory.
- **lessons-kept:** Every mistake an agent makes is logged and becomes a rule or a check, so it doesn't happen twice.
- **measured:** Each item's time and review findings are logged, so we can tell whether the method helps.
- **trivial-path:** A typo or one-line fix goes straight to `main` with a `Trivial:` commit, so small things stay cheap.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `entry-point` | `AGENTS.md`, `CLAUDE.md` | `test_entry_point_claude_md_routes_to_agents_md` |
| `owner-only` | `AGENTS.md`, `.claude/settings.json`, `checks/check.py` | `test_owner_only_secrets_are_caught` |
| `pace` | `AGENTS.md`, `.agents/skills/deliver/SKILL.md` | — |
| `item-first` | `.agents/skills/deliver/SKILL.md`, `checks/check.py` | `test_item_first_malformed_item_fails` |
| `spec-first` | `.agents/skills/deliver/SKILL.md`, `.agents/skills/review/SKILL.md` | — |
| `check-first` | `.agents/skills/deliver/SKILL.md` | — |
| `no-weakening` | `AGENTS.md`, `.agents/skills/review/SKILL.md` | — |
| `blocked-means-ask` | `AGENTS.md`, `.agents/skills/deliver/SKILL.md` | — |
| `checked-before-done` | `.claude/hooks/stop-check.sh`, `.claude/settings.json`, `.githooks/commit-msg` | `test_commit_hook_blocks_red_commits_but_not_check_commits` |
| `try-it` | `.agents/skills/deliver/SKILL.md` | — |
| `fresh-review` | `.agents/skills/review/SKILL.md`, `.agents/skills/deliver/SKILL.md` | — |
| `numbers-traced` | `checks/check.py`, `AGENTS.md` | `test_numbers_traced_wrong_marker_fails`, `test_numbers_traced_unknown_source_fails` |
| `lessons-kept` | `LESSONS.md`, `.agents/skills/debrief/SKILL.md` | — |
| `measured` | `METRICS.md`, `.agents/skills/deliver/SKILL.md` | — |
| `trivial-path` | `AGENTS.md` | — |
