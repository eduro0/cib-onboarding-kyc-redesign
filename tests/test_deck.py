"""Tests for the slide deck (deliverables/deck.pptx).

Implements: package/deck
"""

import json
import re
from pathlib import Path

import sys

import yaml
from pptx import Presentation

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
DECK = ROOT / "deliverables" / "deck.pptx"
TOPICS = ["problem", "as-is", "to-be", "approval", "moments of truth", "kpi", "assistant", "roadmap", "risk", "sources"]


def slides() -> list[str]:
    out = []
    for slide in Presentation(DECK).slides:
        parts = [p.text for shape in slide.shapes if shape.has_text_frame for p in shape.text_frame.paragraphs]
        parts += [c.text for shape in slide.shapes if shape.has_table for row in shape.table.rows for c in row.cells]
        out.append("\n".join(p for p in parts if p.strip()))
    return out


def test_deck_tells_the_story_in_about_twelve_slides():
    texts = slides()
    assert 11 <= len(texts) <= 16  # about twelve; each map takes two slides so it can be read
    titles = " | ".join(" ".join(t.splitlines()[:2]).lower() for t in texts[1:])  # kicker line, then the title
    for topic in TOPICS:
        assert topic in titles, f"no slide title mentions {topic!r}: {titles}"


def test_deck_every_number_comes_from_the_model_or_a_source():
    numbers = json.loads((ROOT / "build" / "numbers.json").read_text())
    allowed = set()
    for v in numbers.values():
        if isinstance(v, (int, float)):
            allowed |= {f"{v:g}", f"{v:.1f}", f"{abs(v):g}", f"{abs(v):.0f}", f"{v * 100:.0f}", f"{abs(v) * 100:.0f}"}
    for path in (ROOT / "sources").glob("*.yaml"):
        for entry in yaml.safe_load(path.read_text()):
            for q in entry["quotes"]:
                allowed |= set(re.findall(r"\d+(?:[.,]\d+)?", q["text"] + " " + str(q.get("locator", "")) + " " + entry["title"]))
    allowed |= {str(n) for n in range(0, 10)}  # list items, phase numbers, M1-M3, P1-P7
    risks = len(re.findall(r"^\| \d+ \|", (ROOT / "docs" / "change-risks.md").read_text(), re.M))
    allowed.add(str(risks))
    roadmap = (ROOT / "docs" / "roadmap.md").read_text()
    for i, text in enumerate(slides(), 1):
        for span in re.findall(r"(?:Weeks|Months) \d+[–-]\d+", text):
            assert span.lower() in roadmap.lower(), f"slide {i}: {span} is not the roadmap's timing"
        body = re.sub(r"\b(19|20)\d\d(-\d\d){0,2}\b", "", text)  # years and dates
        body = re.sub(r"(?:Weeks|Months) \d+[–-]\d+|\b[PM]\d\b|BPMN 2\.0(\.2)?", "", body)
        for token in re.findall(r"\d+(?:[.,]\d+)?", body):
            assert token in allowed or token.replace(",", "") in allowed, f"slide {i}: {token} has no source"


def test_deck_shows_the_maps_and_charts():
    pictures = sum(1 for slide in Presentation(DECK).slides for s in slide.shapes if s.shape_type == 13)
    assert pictures >= 6


def test_deck_map_text_is_readable_on_a_slide():
    # map labels are 11 px in the SVG (PNGs are rendered at 2x); shown full screen at 1920 px wide they must reach 9 px
    px_per_inch = 1920 / 13.333
    checked = 0
    for slide in Presentation(DECK).slides:
        for shape in slide.shapes:
            if shape.shape_type == 13 and shape.image.size[0] > 2500:  # the map halves (charts are 1760 px wide)
                svg_px = shape.image.size[0] / 2
                shown = 11 * (shape.width / 914400 * px_per_inch) / svg_px
                assert shown >= 9, (shape.image.filename, round(shown, 1))
                checked += 1
    assert checked >= 4
