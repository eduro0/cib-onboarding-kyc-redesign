"""Project-agnostic checks behind `make check`.

Implements: workflow/item-first, workflow/numbers-traced, workflow/owner-only

What it fails on, in order:
- spec: malformed statement lines, duplicate names, areas reused across domains, statements with no row in
  "Where this is enforced", rows for unknown statements, enforcer files that don't exist or (for text files) don't
  name the statement back on an `Implements:` line, listed tests that don't exist, `Implements:` lines naming
  unknown statements;
- work items: a missing or unknown status, missing sections, no acceptance boxes, a `done` item with open boxes,
  `Blocked by` naming an item that doesn't exist;
- numbers: a `<!-- check: key = value -->` marker whose key isn't in `build/numbers.json` or whose value differs;
- sources: a `[src:key]` citation with no entry in `sources/*.yaml`, or an entry missing url, quote or date;
- secrets: anything that looks like an API key;
- banned terms: any line of `checks/banned-terms.local.txt` (git-ignored, so the list itself never leaks);
- project checks: every `checks/project/*.py` module's `check(root)` result.

Run from anywhere: `python3 checks/check.py [ROOT]`. Exit 0 when clean, 1 with one line per problem.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

STATEMENT = re.compile(r"^- \*\*([a-z0-9]+(?:-[a-z0-9]+)*):\*\* (\S.*)$")
ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|(.*)\|(.*)\|\s*$")
IMPLEMENTS = re.compile(r"^\s*(?:#|//|<!--|\*|\"\"\")?\s*Implements:\s*([^\n>]*)", re.M)
MARKER = re.compile(r"<!--\s*check:\s*([A-Za-z0-9_.\-/]+)\s*=\s*(.+?)\s*-->")
CITE = re.compile(r"\[src:([a-z0-9][a-z0-9-]*)\]")
SECRET = re.compile(r"(sk-or-v1-[0-9a-f]{20,}|sk-ant-[A-Za-z0-9_\-]{20,}|sk-[A-Za-z0-9]{32,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_\-]{35}|ghp_[A-Za-z0-9]{30,})")
STATUSES = {"ready", "in-progress", "in-review", "done", "blocked", "on-hold"}
ITEM_SECTIONS = ("## Why", "## Deliverable", "## Acceptance", "## Owner does")
TEXT_SUFFIXES = {".md", ".py", ".sh", ".yaml", ".yml", ".toml", ".bpmn", ".xml", ".svg", ".html", ".css", ".js",
                 ".json", ".txt", ".csv", ".cfg", ".ini"}
COMMENTABLE = {".md", ".py", ".sh", ".yaml", ".yml", ".toml", ".bpmn", ".xml", ".html", ".css", ".js"}
NO_IMPLEMENTS_DIRS = ("sources/", "build/", "work/", "reference/")
VERBATIM_LIST = "checks/verbatim-dirs.txt"  # folders whose files are read verbatim (prompts, pasted text): traced by row only
SKIP_SCAN = ("checks/banned-terms.local.txt",)


def files(root: Path) -> list[str]:
    """Tracked plus untracked-but-not-ignored files, relative to root; falls back to a walk outside git."""
    try:
        out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=root, capture_output=True,
                             text=True, check=True).stdout
        return sorted({line for line in out.splitlines() if line and (root / line).is_file()})
    except (subprocess.CalledProcessError, FileNotFoundError):
        return sorted(str(p.relative_to(root)) for p in root.rglob("*")
                      if p.is_file() and ".git" not in p.parts and ".venv" not in p.parts)


def read_text(root: Path, rel: str) -> str | None:
    if Path(rel).suffix.lower() not in TEXT_SUFFIXES and Path(rel).name not in {"Makefile", "CLAUDE.md"}:
        return None
    try:
        return (root / rel).read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def load_spec(root: Path, errors: list[str]) -> dict[str, dict]:
    """Return {"area/name": {"file", "enforced", "tested"}} for every statement in spec/<domain>/<area>.md."""
    statements: dict[str, dict] = {}
    area_domain: dict[str, str] = {}
    for path in sorted((root / "spec").glob("*/*.md")):
        if path.name == "README.md":
            continue
        rel, area, domain = str(path.relative_to(root)), path.stem, path.parent.name
        if area in area_domain and area_domain[area] != domain:
            errors.append(f"{rel}: area '{area}' also exists in spec/{area_domain[area]}/")
        area_domain[area] = domain
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines or not lines[0].startswith("# "):
            errors.append(f"{rel}:1: spec file must start with '# <Area title>'")
        names: dict[str, int] = {}
        rows: dict[str, tuple[str, str]] = {}
        in_table = False
        for n, line in enumerate(lines, 1):
            if line.startswith("## Where this is enforced"):
                in_table = True
                continue
            if in_table:
                m = ROW.match(line)
                if m and m.group(1) != "Statement":
                    rows[m.group(1)] = (m.group(2).strip(), m.group(3).strip())
                continue
            if line.startswith("- **"):
                m = STATEMENT.match(line)
                if not m:
                    errors.append(f"{rel}:{n}: statement must read '- **lowercase-name:** sentence'")
                elif m.group(1) in names:
                    errors.append(f"{rel}:{n}: duplicate statement '{m.group(1)}' (first on line {names[m.group(1)]})")
                else:
                    names[m.group(1)] = n
        if not in_table and names:
            errors.append(f"{rel}: missing '## Where this is enforced' table")
        for name, n in names.items():
            if name not in rows:
                errors.append(f"{rel}:{n}: '{name}' has no row in 'Where this is enforced'")
                continue
            statements[f"{area}/{name}"] = {"file": rel, "enforced": rows[name][0], "tested": rows[name][1]}
        for name in rows:
            if name not in names:
                errors.append(f"{rel}: table row '{name}' names no statement")
    return statements


def implemented(text: str) -> set[str]:
    """Statement IDs named on a file's `Implements:` lines, whatever the comment syntax around them."""
    return {t for m in IMPLEMENTS.finditer(text) for t in re.findall(r"[a-z0-9-]+/[a-z0-9-]+", m.group(1))}


def ticked(cell: str) -> list[str]:
    return re.findall(r"`([^`]+)`", cell)


def no_implements(root: Path) -> tuple[str, ...]:
    path = root / VERBATIM_LIST
    extra = [d.strip().rstrip("/") + "/" for d in path.read_text().splitlines()
             if d.strip() and not d.startswith("#")] if path.exists() else []
    return NO_IMPLEMENTS_DIRS + tuple(extra)


def check_trace(root: Path, all_files: list[str], statements: dict[str, dict], errors: list[str]) -> None:
    skip = no_implements(root)
    test_names = set()
    for rel in all_files:
        if rel.endswith(".py") and (rel.startswith("tests/") or rel.startswith("checks/")):
            test_names |= set(re.findall(r"^\s*def (\w+)\(", (root / rel).read_text(encoding="utf-8"), re.M))
    for sid, row in statements.items():
        where = row["file"]
        enforced = row["enforced"]
        if not enforced:
            errors.append(f"{where}: '{sid}' names no enforcer (write `not yet`, `reviewer`, `owner` or files)")
        for target in ticked(enforced):
            matches = sorted(root.glob(target)) if any(c in target for c in "*?[") else [root / target]
            if not any(p.exists() for p in matches):
                errors.append(f"{where}: '{sid}' is enforced by '{target}', which doesn't exist")
                continue
            for p in matches:
                if p.is_file() and p.suffix in COMMENTABLE and not str(p.relative_to(root)).startswith(skip):
                    text = p.read_text(encoding="utf-8", errors="replace")
                    named = implemented(text)
                    if sid not in named:
                        errors.append(f"{p.relative_to(root)}: enforces '{sid}' but its Implements: line doesn't name it")
        for test in ticked(row["tested"]):
            if test not in test_names:
                errors.append(f"{where}: '{sid}' is tested by '{test}', which doesn't exist in tests/ or checks/")
    for rel in all_files:
        text = read_text(root, rel)
        if text is None or rel.startswith(skip):
            continue
        for token in implemented(text):
            if token not in statements:
                errors.append(f"{rel}: Implements: names unknown statement '{token}'")


def check_work(root: Path, errors: list[str]) -> None:
    items = {p.name[:3]: p for p in sorted((root / "work").glob("[0-9][0-9][0-9]-*.md"))}
    for num, path in items.items():
        rel, text = str(path.relative_to(root)), path.read_text(encoding="utf-8")
        m = re.search(r"^status:\s*(\S+)", text, re.M)
        if not m or m.group(1) not in STATUSES:
            errors.append(f"{rel}: needs a 'status:' line, one of {', '.join(sorted(STATUSES))}")
        for section in ITEM_SECTIONS:
            if not re.search(rf"^{re.escape(section)}\b", text, re.M):
                errors.append(f"{rel}: missing section '{section}'")
        acceptance = re.search(r"^## Acceptance\b(.*?)(?=^## |\Z)", text, re.M | re.S)
        boxes = re.findall(r"^- \[( |x)\]", acceptance.group(1), re.M) if acceptance else []
        if not boxes:
            errors.append(f"{rel}: '## Acceptance' needs at least one '- [ ]' box")
        if m and m.group(1) == "done" and " " in boxes:
            errors.append(f"{rel}: status is done but {boxes.count(' ')} acceptance box(es) are open")
        for dep in re.findall(r"^Blocked by:\s*(.+)$", text, re.M):
            for ref in re.findall(r"\d{3}", dep):
                if ref not in items:
                    errors.append(f"{rel}: blocked by {ref}, which isn't in work/")


def same(expected: object, written: str) -> bool:
    try:
        return abs(float(str(expected).replace(",", "")) - float(written.replace(",", "").rstrip("%"))) < 1e-9
    except ValueError:
        return str(expected) == written


def check_numbers_and_sources(root: Path, all_files: list[str], errors: list[str]) -> None:
    numbers_path = root / "build" / "numbers.json"
    numbers = json.loads(numbers_path.read_text()) if numbers_path.exists() else None
    keys = load_source_keys(root, errors)
    for rel in all_files:
        if rel.startswith(("checks/", "tests/", "reference/")):
            continue
        text = read_text(root, rel)
        if text is None:
            continue
        for m in MARKER.finditer(text):
            if m.start() > 0 and text[m.start() - 1] == "`":
                continue  # an example in prose, not a claim
            line = text.count("\n", 0, m.start()) + 1
            if numbers is None:
                errors.append(f"{rel}:{line}: check marker but no build/numbers.json (run `make build`)")
            elif m.group(1) not in numbers:
                errors.append(f"{rel}:{line}: check marker key '{m.group(1)}' isn't in build/numbers.json")
            elif not same(numbers[m.group(1)], m.group(2)):
                errors.append(f"{rel}:{line}: '{m.group(1)}' is {numbers[m.group(1)]}, text says {m.group(2)}")
        if rel.startswith("sources/"):
            continue
        for m in CITE.finditer(text):
            if m.start() > 0 and text[m.start() - 1] == "`":
                continue
            if m.group(1) not in keys:
                line = text.count("\n", 0, m.start()) + 1
                errors.append(f"{rel}:{line}: cites [src:{m.group(1)}], which isn't in sources/")


def load_source_keys(root: Path, errors: list[str]) -> set[str]:
    keys: set[str] = set()
    paths = sorted((root / "sources").glob("*.yaml")) if (root / "sources").exists() else []
    if not paths:
        return keys
    try:
        import yaml
    except ImportError:
        errors.append("sources/: PyYAML is needed to read sources (run through `make check`)")
        return keys
    for path in paths:
        for entry in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
            key = entry.get("key", "?")
            if key in keys:
                errors.append(f"{path.relative_to(root)}: duplicate source key '{key}'")
            keys.add(key)
            missing = [f for f in ("url", "date_accessed") if not entry.get(f)]
            if not entry.get("quotes"):
                missing.append("quotes")
            if missing:
                errors.append(f"{path.relative_to(root)}: source '{key}' is missing {', '.join(missing)}")
    return keys


def check_secrets_and_terms(root: Path, all_files: list[str], errors: list[str]) -> None:
    terms_path = root / "checks" / "banned-terms.local.txt"
    terms = []
    if terms_path.exists():
        terms = [t.strip() for t in terms_path.read_text().splitlines() if t.strip() and not t.startswith("#")]
    for rel in all_files:
        if rel in SKIP_SCAN:
            continue
        text = read_text(root, rel)
        if text is None:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if SECRET.search(line):
                errors.append(f"{rel}:{n}: looks like an API key; keys live in .env only")
            low = line.lower()
            for term in terms:
                if term.lower() in low:
                    errors.append(f"{rel}:{n}: banned term (see checks/banned-terms.local.txt)")


def run_project_checks(root: Path, errors: list[str]) -> None:
    for path in sorted((root / "checks" / "project").glob("*.py")):
        if path.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(f"project_check_{path.stem}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, "check"):
            errors.extend(f"[{path.stem}] {e}" for e in module.check(root))


def run(root: Path) -> list[str]:
    errors: list[str] = []
    all_files = files(root)
    statements = load_spec(root, errors)
    check_trace(root, all_files, statements, errors)
    check_work(root, errors)
    check_numbers_and_sources(root, all_files, errors)
    check_secrets_and_terms(root, all_files, errors)
    run_project_checks(root, errors)
    return errors


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent).resolve()
    errors = run(root)
    pending = sum(1 for p in (root / "spec").glob("*/*.md") for line in p.read_text().splitlines()
                  if ROW.match(line) and "not yet" in line)
    for e in errors:
        print(e)
    status = "FAIL" if errors else "ok"
    print(f"check: {status} ({len(errors)} problem(s), {pending} statement(s) marked `not yet`)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
