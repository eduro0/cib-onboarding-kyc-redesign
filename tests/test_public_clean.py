"""Tests for checks/project/public_clean.py.

Implements: constraints/no-firm-names, constraints/simulated-labelled, constraints/sourced-claims, constraints/no-private-people
"""

import importlib.util
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("public_clean", ROOT / "checks" / "project" / "public_clean.py")
public_clean = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(public_clean)


def project(tmp_path: Path, numbers: dict | None = None) -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / "deliverables").mkdir()
    (tmp_path / "checks").mkdir()
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "numbers.json").write_text(json.dumps(numbers or {"cycle_days_as_is": 41.7}))
    return tmp_path


def slide_deck(path: Path, slides: list[str]) -> None:
    """A minimal .pptx-shaped zip: one XML part per slide with the text in an a:t element."""
    with zipfile.ZipFile(path, "w") as z:
        for i, text in enumerate(slides, 1):
            z.writestr(f"ppt/slides/slide{i}.xml", f"<p:sld><a:t>{text}</a:t></p:sld>")


def test_clean_project_passes(tmp_path):
    root = project(tmp_path)
    (root / "docs" / "roadmap.md").write_text("Cycle time falls from 41.7 days (simulated).\n")
    assert public_clean.check(root) == []


def test_no_firm_names_term_in_a_deck_fails(tmp_path):
    root = project(tmp_path)
    (root / "checks" / "banned-terms.local.txt").write_text("Pilot Firm Ltd\n")
    slide_deck(root / "deliverables" / "deck.pptx", ["Lessons from pilot firm ltd"])
    assert any("deck.pptx" in e and "banned" in e for e in public_clean.check(root))


def test_no_private_people_local_term_in_docs_fails(tmp_path):
    root = project(tmp_path)
    (root / "checks" / "public-terms.local.txt").write_text("Jane Referrer\n")
    (root / "docs" / "site-pack.md").write_text("Thanks to Jane Referrer.\n")
    assert any("site-pack.md:1" in e and "private" in e for e in public_clean.check(root))


def test_simulated_labelled_number_without_label_fails(tmp_path):
    root = project(tmp_path)
    (root / "docs" / "roadmap.md").write_text("Cycle time is 41.7 days.\n")
    assert any("roadmap.md" in e and "simulated" in e for e in public_clean.check(root))


def test_simulated_labelled_each_slide_is_checked(tmp_path):
    root = project(tmp_path)
    slide_deck(root / "deliverables" / "deck.pptx", ["Simulated: 41.7 days", "Before: 41.7 days"])
    errors = public_clean.check(root)
    assert len([e for e in errors if "simulated" in e]) == 1 and "slide2" in errors[0]


def test_sourced_claims_regulator_paragraph_without_citation_fails(tmp_path):
    root = project(tmp_path)
    (root / "docs" / "change-risks.md").write_text(
        "The HKMA expects a risk-based approach [src:hkma-aml-guideline].\n\n"
        "The HKMA also wants reviews every year.\n")
    errors = public_clean.check(root)
    assert len(errors) == 1 and "change-risks.md:3" in errors[0] and "cite" in errors[0]


def office_file(path: Path, parts: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w") as z:
        for name, xml in parts.items():
            z.writestr(name, xml)


def test_no_firm_names_found_in_notes_properties_and_split_runs(tmp_path):
    root = project(tmp_path)
    (root / "checks" / "banned-terms.local.txt").write_text("Pilot Firm & Co\n")
    office_file(root / "deliverables" / "notes.pptx", {"ppt/slides/slide1.xml": "<a:t>Clean</a:t>",
                                                      "ppt/notesSlides/notesSlide1.xml": "<a:t>From Pilot Firm &amp; Co</a:t>"})
    office_file(root / "deliverables" / "props.docx", {"word/document.xml": "<w:t>Clean</w:t>",
                                                      "docProps/core.xml": "<dc:creator>Pilot Firm &amp; Co</dc:creator>"})
    office_file(root / "deliverables" / "split.pptx", {"ppt/slides/slide1.xml": "<a:p><a:r><a:t>Pilot Fi</a:t></a:r><a:r><a:t>rm &amp; Co</a:t></a:r></a:p>"})
    errors = [e for e in public_clean.check(root) if "banned" in e]
    assert {e.split(":")[0] for e in errors} == {"deliverables/notes.pptx", "deliverables/props.docx", "deliverables/split.pptx"}


def test_sourced_claims_source_of_wealth_is_not_a_citation(tmp_path):
    root = project(tmp_path)
    slide_deck(root / "deliverables" / "deck.pptx", ["The HKMA expects source of wealth checks for PEPs"])
    assert any("slide1" in e and "source" in e for e in public_clean.check(root))
    slide_deck(root / "deliverables" / "deck.pptx", ["The HKMA expects it. Source: HKMA AML/CFT Guideline"])
    assert public_clean.check(root) == []


def test_sourced_claims_spelled_out_regulators_need_a_citation(tmp_path):
    root = project(tmp_path)
    (root / "docs" / "a.md").write_text("The Hong Kong Monetary Authority says so.\n\nThe companies ordinance requires it.\n\n"
                                        "The Securities and Futures Commission agrees.\n")
    assert len([e for e in public_clean.check(root) if "cite" in e]) == 3


def test_sourced_claims_only_listed_fictional_samples_are_exempt(tmp_path):
    root = project(tmp_path)
    (root / "deliverables" / "gem").mkdir()
    (root / "deliverables" / "gem" / "sample-pack-acme.md").write_text("ISSUER: Companies Registry (fictional)\n")
    (root / "docs" / "claims.md").write_text("<!-- fictional sample: no citations -->\nThe HKMA says so.\n")
    errors = public_clean.check(root)
    assert len(errors) == 1 and errors[0].startswith("docs/claims.md")
