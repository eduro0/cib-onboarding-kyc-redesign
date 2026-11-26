"""Tests for the kit's own checks (checks/check.py).

Implements: workflow/entry-point, workflow/owner-only, workflow/item-first, workflow/numbers-traced
"""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "checks"))
import check  # noqa: E402

GOOD_ITEM = """# 001 Make the thing
status: ready

## Why
Because.

## Deliverable
The thing.

## Acceptance
- [ ] the thing exists

## Owner does
Nothing.
"""


def make_project(tmp_path: Path) -> Path:
    """A minimal clean project: one spec area, one work item."""
    (tmp_path / "spec" / "product").mkdir(parents=True)
    (tmp_path / "work").mkdir()
    (tmp_path / "spec" / "product" / "thing.md").write_text(
        "# Thing\n\n- **exists:** The thing exists.\n\n## Where this is enforced\n\n"
        "| Statement | Enforced by | Tested by |\n|---|---|---|\n| `exists` | not yet | — |\n")
    (tmp_path / "work" / "001-thing.md").write_text(GOOD_ITEM)
    return tmp_path


def test_clean_project_passes(tmp_path):
    assert check.run(make_project(tmp_path)) == []


def test_entry_point_claude_md_routes_to_agents_md():
    assert (ROOT / "CLAUDE.md").read_text().strip().endswith("@AGENTS.md")
    assert (ROOT / "AGENTS.md").exists()


def test_owner_only_secrets_are_caught(tmp_path):
    root = make_project(tmp_path)
    fake = "sk-or-v1-" + "ab" * 16
    (root / "notes.md").write_text(f"key = {fake}\n")
    assert any("API key" in e for e in check.run(root))


def test_banned_terms_are_caught_and_the_list_itself_is_skipped(tmp_path):
    root = make_project(tmp_path)
    (root / "checks").mkdir()
    (root / "checks" / "banned-terms.local.txt").write_text("Acme Secret Corp\n")
    (root / "deck.md").write_text("We did this for acme secret corp.\n")
    errors = check.run(root)
    assert any("deck.md:1: banned term" in e for e in errors)
    assert not any(e.startswith("checks/banned-terms.local.txt") for e in errors)


def test_item_first_malformed_item_fails(tmp_path):
    root = make_project(tmp_path)
    (root / "work" / "002-bad.md").write_text("# 002 Bad\nstatus: someday\n")
    errors = check.run(root)
    assert any("002-bad.md: needs a 'status:' line" in e for e in errors)
    assert any("missing section '## Acceptance'" in e for e in errors)


def test_item_first_done_with_open_boxes_fails(tmp_path):
    root = make_project(tmp_path)
    (root / "work" / "001-thing.md").write_text(GOOD_ITEM.replace("status: ready", "status: done"))
    assert any("acceptance box(es) are open" in e for e in check.run(root))


def test_spec_statement_without_row_fails(tmp_path):
    root = make_project(tmp_path)
    spec = root / "spec" / "product" / "thing.md"
    spec.write_text(spec.read_text().replace("- **exists:**", "- **exists:** x\n- **orphan:** No row.\n- **exists2:**"))
    errors = check.run(root)
    assert any("'orphan' has no row" in e for e in errors)


def test_enforcer_must_point_back(tmp_path):
    root = make_project(tmp_path)
    spec = root / "spec" / "product" / "thing.md"
    spec.write_text(spec.read_text().replace("| `exists` | not yet |", "| `exists` | `make.py` |"))
    (root / "make.py").write_text("print('hi')\n")
    assert any("Implements: line doesn't name it" in e for e in check.run(root))
    (root / "make.py").write_text("# Implements: thing/exists\nprint('hi')\n")
    assert check.run(root) == []


def test_numbers_traced_wrong_marker_fails(tmp_path):
    root = make_project(tmp_path)
    (root / "build").mkdir()
    (root / "build" / "numbers.json").write_text(json.dumps({"cycle_days": 42.5}))
    (root / "deck.md").write_text("Cycle time <!-- check: cycle_days = 42.5 --> days.\n")
    assert check.run(root) == []
    (root / "deck.md").write_text("Cycle time <!-- check: cycle_days = 40 --> days.\n")
    assert any("'cycle_days' is 42.5, text says 40" in e for e in check.run(root))


def test_numbers_traced_unknown_source_fails(tmp_path):
    root = make_project(tmp_path)
    (root / "sources").mkdir()
    (root / "sources" / "rules.yaml").write_text(
        "- key: real-rule\n  url: https://example.org\n  date_accessed: 2026-11-18\n"
        "  quotes:\n    - text: a quote\n")
    (root / "deck.md").write_text("As the rule says [src:real-rule], and [src:made-up].\n")
    errors = check.run(root)
    assert len(errors) == 1 and "[src:made-up]" in errors[0]


def test_project_checks_are_run(tmp_path):
    root = make_project(tmp_path)
    (root / "checks" / "project").mkdir(parents=True)
    (root / "checks" / "project" / "always_fails.py").write_text("def check(root):\n    return ['nope']\n")
    assert "[always_fails] nope" in check.run(root)


def test_template_itself_passes(tmp_path):
    if any((ROOT / "spec" / "product").glob("*.md")):
        return  # a real project: `make check` covers it
    copy = tmp_path / "copy"
    shutil.copytree(ROOT, copy, symlinks=True,
                    ignore=shutil.ignore_patterns(".git", ".venv", ".pytest_cache", "__pycache__", "*.local.*"))
    assert check.run(copy) == []


def test_verbatim_dirs_are_traced_by_row_only(tmp_path):
    root = make_project(tmp_path)
    spec = root / "spec" / "product" / "thing.md"
    spec.write_text(spec.read_text().replace("| `exists` | not yet |", "| `exists` | `prompts/ask.md` |"))
    (root / "prompts").mkdir()
    (root / "prompts" / "ask.md").write_text("Exactly what the model reads.\n")
    assert any("Implements: line doesn't name it" in e for e in check.run(root))
    (root / "checks").mkdir()
    (root / "checks" / "verbatim-dirs.txt").write_text("prompts/\n")
    assert check.run(root) == []


def test_commit_hook_blocks_red_commits_but_not_check_commits(tmp_path):
    import subprocess
    hook = ROOT / ".githooks" / "commit-msg"
    (tmp_path / "Makefile").write_text("check:\n\t@exit 1\n")
    msg = tmp_path / "msg"
    run = lambda text: (msg.write_text(text), subprocess.run([str(hook), str(msg)], cwd=tmp_path, capture_output=True))[1]
    assert run("Build: something\n").returncode == 1
    assert run("Check: a failing test\n").returncode == 0
    (tmp_path / "Makefile").write_text("check:\n\t@exit 0\n")
    assert run("Build: something\n").returncode == 0
