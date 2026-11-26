"""Public-safety checks on everything a reader outside the project will see: `docs/` and `deliverables/`.

Implements: constraints/no-firm-names, constraints/simulated-labelled, constraints/sourced-claims, constraints/no-private-people

The kit's check.py already scans text files for the banned terms. This module adds what it can't see:
- the text inside generated Office files (.pptx slides, .xlsx sheets), so a banned term can't hide in a deck;
- private terms (people, recruiting details) from `checks/public-terms.local.txt`, applied to public folders only,
  so internal notes outside those folders may still name them;
- simulated labels: a page (a Markdown file, a slide, a sheet) showing a number from `build/numbers.json`, or
  carrying a check marker, must say "simulated" on that same page;
- citations: a Markdown paragraph, or a slide, that names a regulator or rulebook (abbreviated or spelled out) must
  cite `[src:key]`; a slide may instead carry a line starting "Source:". The fictional sample packs listed in
  FICTIONAL_SAMPLES are the only exemption.

Office files are read part by part (slides, notes, masters, charts, headers, comments, document properties), with
text runs joined so a term Office split in two is still found.

Limit: the simulated-label rule recognises a number only if it is in build/numbers.json (in a distinctive form:
three or more digits, or a decimal) or carries a check marker.
A number typed by hand from nowhere is caught by review, not here.
"""

from __future__ import annotations

import fnmatch
import html
import json
import re
import zipfile
from pathlib import Path

PUBLIC = ("docs", "deliverables")
REGULATOR = re.compile(r"\b(HKMA|AMLO|MAS|FATF|SFC|PCPD)\b|\b(Hong Kong Monetary Authority|Monetary Authority of Singapore|"
                       r"Securities and Futures Commission|Anti-Money Laundering and Counter-Terrorist Financing Ordinance|"
                       r"Companies Ordinance|Companies Registry|Wolfsberg|Financial Action Task Force|Cap\. ?6(15|22)|"
                       r"Notice 626)\b", re.I)
# Made-up documents for the demo make no claims about the world, so they need no citations. Listed by path, so no
# other file can exempt itself.
FICTIONAL_SAMPLES = ("deliverables/gem/sample-pack-*.md",)
CITED_SLIDE = re.compile(r"\[src:|(^|\s)Sources?:", re.M)
TEXT = {".md", ".txt", ".svg", ".bpmn", ".html", ".csv", ".yaml", ".json"}


def terms(root: Path, name: str) -> list[str]:
    path = root / "checks" / name
    if not path.exists():
        return []
    return [t.strip().lower() for t in path.read_text().splitlines() if t.strip() and not t.startswith("#")]


def renderings(numbers: dict) -> set[str]:
    """The ways a model number can appear in prose: as written, rounded, or as a percentage of a share."""
    out: set[str] = set()
    for value in numbers.values():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        forms = {f"{value:g}", f"{value:.1f}", f"{value:,.0f}" if abs(value) >= 1000 else ""}
        if 0 < value < 1:
            forms |= {f"{value * 100:.0f}%", f"{value * 100:.1f}%"}
        # A rendering counts only if it is distinctive: three or more digits, or a decimal point. Two-digit
        # percentages ("30%") are everywhere in KYC text (ownership stakes), so they would raise false alarms.
        out |= {f for f in forms if f and (sum(ch.isdigit() for ch in f) >= 3 or "." in f) and f not in {"0.0", "1.0"}}
    return out


def pages(root: Path) -> list[tuple[str, str]]:
    """(label, text) for every public page: a text file, a slide, a sheet or a Word body."""
    found: list[tuple[str, str]] = []
    for folder in PUBLIC:
        for path in sorted((root / folder).rglob("*")) if (root / folder).exists() else []:
            rel = str(path.relative_to(root))
            if not path.is_file():
                continue
            if path.suffix in TEXT:
                found.append((rel, path.read_text(encoding="utf-8", errors="replace")))
            elif path.suffix in {".pptx", ".docx"}:
                with zipfile.ZipFile(path) as z:
                    for part in sorted(n for n in z.namelist() if n.endswith(".xml") or n.endswith(".rels")):
                        found.append((f"{rel}:{Path(part).stem}", xml_text(z.read(part).decode("utf-8", errors="replace"))))
            elif path.suffix == ".xlsx":
                from openpyxl import load_workbook
                wb = load_workbook(path, read_only=True, data_only=True)
                for ws in wb.worksheets:
                    cells = [str(c) for row in ws.iter_rows(values_only=True) for c in row if c is not None]
                    found.append((f"{rel}:{ws.title}", " ".join(cells)))
    return found


def xml_text(xml: str) -> str:
    """Readable text of one Office XML part: runs joined within a paragraph (Office splits words across runs),
    paragraphs on their own lines, entities unescaped. Parts with no text runs (properties) give their raw text."""
    paragraphs = re.findall(r"<(?:a|w):p[ >].*?</(?:a|w):p>", xml, re.S)
    if paragraphs:
        lines = ["".join(re.findall(r"<(?:a|w):t(?:\s[^>]*)?>([^<]*)</(?:a|w):t>", p)) for p in paragraphs]
    else:
        runs = re.findall(r"<(?:a|w):t(?:\s[^>]*)?>([^<]*)</(?:a|w):t>", xml)
        lines = runs or [re.sub(r"<[^>]+>", " ", xml)]
    return html.unescape("\n".join(lines))


def check(root: Path) -> list[str]:
    errors: list[str] = []
    banned, private = terms(root, "banned-terms.local.txt"), terms(root, "public-terms.local.txt")
    numbers_path = root / "build" / "numbers.json"
    shown = renderings(json.loads(numbers_path.read_text())) if numbers_path.exists() else set()
    for label, text in pages(root):
        low = text.lower()
        lines = text.splitlines() or [text]
        for term in banned:
            if term in low and not label.split(":")[0].endswith((".md", ".svg", ".bpmn", ".txt")):
                errors.append(f"{label}: banned term inside a generated file (see checks/banned-terms.local.txt)")
        for term in private:
            for n, line in enumerate(lines, 1):
                if term in line.lower():
                    errors.append(f"{label}:{n}: private term in a public file (see checks/public-terms.local.txt)")
        has_number = "<!-- check:" in text or any(re.search(rf"(?<![\d.]){re.escape(f)}(?![\d])", text) for f in shown)
        if has_number and "simulated" not in low:
            errors.append(f"{label}: shows a model number but never says it is simulated")
        if label.endswith(".md") and not any(fnmatch.fnmatch(label, g) for g in FICTIONAL_SAMPLES):
            line_no = 1
            for para in re.split(r"\n\s*\n", text):
                if REGULATOR.search(para) and "[src:" not in para:
                    errors.append(f"{label}:{line_no}: names a regulator or rulebook but doesn't cite a source")
                line_no += para.count("\n") + 2
        elif re.search(r":(slide|notesSlide)\d+$", label) and REGULATOR.search(text) and not CITED_SLIDE.search(text):
            errors.append(f"{label}: names a regulator or rulebook but has no source line")
    return errors
