"""Tests for the tool packs (Data Studio, Gemini Notebook, Google Sites) and the owner checklist.

Implements: package/dashboard-guide, package/notebook-pack, package/site-pack, package/owner-checklist
"""

import re
from pathlib import Path

import yaml
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


def source_urls() -> set[str]:
    return {e["url"] for p in (ROOT / "sources").glob("*.yaml") for e in yaml.safe_load(p.read_text())}


def test_dashboard_guide_names_fields_that_exist_in_the_looker_tab():
    guide = (DOCS / "dashboard-guide.md").read_text()
    ws = load_workbook(ROOT / "deliverables" / "kpi-model.xlsx", read_only=True)["Looker data"]
    header = [c for c in next(ws.iter_rows(min_row=2, max_row=2, values_only=True))]
    kpis = {r[3] for r in ws.iter_rows(min_row=3, values_only=True)}
    charts = re.findall(r"^### Chart \d+", guide, re.M)
    assert len(charts) >= 4
    for field in header:
        assert f"`{field}`" in guide, field
    for kpi in re.findall(r"KPI = `([^`]+)`", guide):
        assert kpi in kpis, kpi
    assert "A2:E" in guide and "simulated" in guide.lower()


def test_notebook_pack_loads_only_recorded_sources_and_asks_five_questions():
    pack = (DOCS / "notebook-pack.md").read_text()
    urls = set(re.findall(r"<(https://[^>]+)>", pack))
    assert len(urls) >= 8 and urls <= source_urls()
    assert len(re.findall(r"^\d+\. \*\*Ask:\*\*", pack, re.M)) == 5


def test_site_pack_has_every_page_and_links_every_deliverable():
    pack = (DOCS / "site-pack.md").read_text()
    pages = re.findall(r"^## Page \d+: (.+)$", pack, re.M)
    assert len(pages) >= 5
    for item in ("deck.pptx", "kpi-model.xlsx", "as-is.bpmn", "to-be.bpmn", "roadmap.docx", "change-risks.docx"):
        assert item in pack, item
    assert "assistant" not in "".join(pages).lower()  # the owner dropped the assistant page


def test_owner_checklist_covers_every_owner_step_in_order_with_times():
    checklist = (DOCS / "owner-checklist.md").read_text()
    steps = re.findall(r"^(\d+)\. \*\*(.+?)\*\* \((\d+) min\)", checklist, re.M)
    assert [int(s[0]) for s in steps] == list(range(1, len(steps) + 1)) and len(steps) >= 7
    for item in sorted((ROOT / "work").glob("[0-9][0-9][0-9]-*.md")):
        owner = item.read_text().split("## Owner does", 1)[1].split("\n## ", 1)[0]
        for term in re.findall(r"`([^`]+)`", owner):  # every file, key or tool an owner step names
            if term != "docs/owner-checklist.md":
                assert term in checklist or term.split("/")[-1] in checklist, f"{item.name}: {term} missing from the checklist"
    for step in ("Save as Google Slides", "Save as Google Docs", "Anyone with the link"):
        assert step in checklist, step


def test_dashboard_guide_never_sums_across_processes_or_case_types():
    guide = (DOCS / "dashboard-guide.md").read_text()
    for chart in re.split(r"^### ", guide, flags=re.M)[1:]:
        if "Dimension: `Case`" in chart:
            assert "`Process`" in chart and "Average" in chart, chart[:40]
    assert "default selection" in guide.lower() and "onboarding" in guide
