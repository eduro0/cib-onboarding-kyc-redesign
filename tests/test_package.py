"""Tests for the written package: roadmap, change-risk register and their Google Docs exports.

Implements: package/roadmap, package/change-risks
"""

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
sys.path.insert(0, str(ROOT / "scripts"))


def test_roadmap_each_phase_says_what_ships_who_agrees_and_its_gate():
    text = (DOCS / "roadmap.md").read_text()
    phases = re.split(r"^## Phase ", text, flags=re.M)[1:]
    assert len(phases) >= 4
    for phase in phases:
        for part in ("**What ships.**", "**Who agrees.**", "**Gate"):
            assert part in phase, (part, phase[:40])


def test_change_risks_register_covers_every_area_with_every_field():
    text = (DOCS / "change-risks.md").read_text()
    rows = [r for r in text.splitlines() if re.match(r"^\| \d+ \|", r)]
    assert len(rows) >= 8
    areas = set()
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        assert len(cells) == 8 and all(cells), row  # #, risk, area, likelihood, impact, mitigation, owner, signal
        assert cells[3] in {"High", "Medium", "Low"} and cells[4] in {"High", "Medium", "Low"}, row
        areas.add(cells[2])
    assert {"Staff", "Clients", "Controls", "Regulators", "Technology"} <= areas


def test_docs_export_to_word_with_numbered_sources_and_real_lists(tmp_path):
    import build
    build.build_docs(tmp_path)
    for name in ("roadmap", "change-risks"):
        reader = build.for_readers((DOCS / f"{name}.md").read_text(), build.sources())
        keys = build.cited(DOCS / f"{name}.md")
        listed = re.findall(r"^\d+\. .*<https://", reader.split("## Sources")[-1], re.M)
        assert keys and len(listed) == len(keys), name
        assert max(int(n) for n in re.findall(r"\[(\d+)\]", reader)) == len(keys)
        with zipfile.ZipFile(tmp_path / f"{name}.docx") as z:
            xml = z.read("word/document.xml").decode()
        text = " ".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", xml))
        assert "[src:" not in text and "check:" not in text and "https://" in text
        if name == "roadmap":
            assert xml.count("<w:numPr>") >= 10, "bullet lists merged into paragraphs"
        assert (tmp_path / f"{name}.docx").read_bytes() == (ROOT / "deliverables" / "docs" / f"{name}.docx").read_bytes(), \
            f"{name}.docx is stale or not reproducible: run make build"
