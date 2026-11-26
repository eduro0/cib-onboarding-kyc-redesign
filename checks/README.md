# Checks

`check.py` holds the project-agnostic checks (spec, work items, numbers, sources, secrets, banned terms); its
docstring lists them. Project-specific checks go in `project/`, one module each with `check(root) -> list[str]`;
`check.py` runs them all. `banned-terms.local.txt` (git-ignored) lists words that must never appear, one per line.
