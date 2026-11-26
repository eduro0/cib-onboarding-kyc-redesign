"""The slide deck (deliverables/deck.pptx), for Google Slides: File > Import slides, or open the .pptx from Drive.

Implements: package/deck

Thirteen slides tell the story in the order a reviewer asks the questions: what's wrong, what we looked at, how it
works today, how it should work, where people stay in control, what the client feels, what it's worth, what was
built, how to roll it out, what could go wrong, and where every fact comes from. Every number is read from
build/numbers.json or quoted from sources/; every slide that shows a model number says it is simulated, and every
slide that names a regulator carries a "Source:" line.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
INK, INK_2, MUTED, LINE = RGBColor(0x16, 0x1B, 0x24), RGBColor(0x45, 0x4D, 0x59), RGBColor(0x6B, 0x72, 0x7D), RGBColor(0xD9, 0xDE, 0xE5)
BLUE, ORANGE, GREEN, PALE = RGBColor(0x2A, 0x78, 0xD6), RGBColor(0xEB, 0x68, 0x34), RGBColor(0x1F, 0x7A, 0x4D), RGBColor(0xF3, 0xF5, 0xF8)
W, H = Inches(13.333), Inches(7.5)
MAP_WIDTH_IN = 12.45
# Each map is shown in two halves so its text can be read: (first column, last column, title, note at each cut)
HALVES = {"as-is": [(0, 9, "intake, documents, data and ownership", "", "continues on the next slide →"),
                    (10, 20, "risk rating, EDD, QC and sign-off", "← from the previous slide", "")],
          "to-be": [(0, 11, "AI pre-fill, one request, AI reading, screening", "", "continues on the next slide →"),
                    (12, 24, "risk, EDD, pre-QC and sign-off", "← from the previous slide", "")]}
SIM = "Simulated figures: an illustrative model, every input a labelled guess; not real bank data."
TOUCHES = ("Client touches = separate requests for documents per case, not every contact (surveys that count all "
           "interactions report more).")


def text(slide, x, y, w, h, lines, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT, font="Calibri", space=6):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines if isinstance(lines, list) else [lines]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        runs = line if isinstance(line, list) else [(line, bold)]
        for chunk, b in runs:
            r = p.add_run()
            r.text = chunk
            r.font.size, r.font.bold, r.font.color.rgb, r.font.name = Pt(size), b, color, font
        p.alignment = align
        p.space_after = Pt(space)
    return box


def page(prs, title, kicker=None, footer=None, source=None, footer_y=6.85):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bar = slide.shapes.add_shape(1, 0, 0, Inches(0.18), H)
    bar.fill.solid(); bar.fill.fore_color.rgb = BLUE; bar.line.fill.background()
    if kicker:
        text(slide, Inches(0.6), Inches(0.35), Inches(12), Inches(0.4), kicker.upper(), size=12, color=BLUE, bold=True)
    text(slide, Inches(0.6), Inches(0.65), Inches(12.2), Inches(0.9), title, size=28, bold=True)
    notes = [n for n in (source and f"Source: {source}", footer) if n]
    if notes:
        text(slide, Inches(0.6), Inches(footer_y), Inches(12.2), Inches(0.4), notes, size=10, color=MUTED, space=0)
    return slide


def bullets(slide, x, y, w, h, items, size=17):
    return text(slide, x, y, w, h, [[("•  ", False)] + ([(i, False)] if isinstance(i, str) else i) for i in items], size=size, color=INK_2, space=10)


def table(slide, x, y, w, rows, widths, size=12, header_fill=BLUE, row_h=0.45):
    shape = slide.shapes.add_table(len(rows), len(rows[0]), x, y, w, Inches(row_h * len(rows)))
    tbl = shape.table
    for c, width in enumerate(widths):
        tbl.columns[c].width = Emu(int(w * width))
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            cell = tbl.cell(r, c)
            cell.text = value
            cell.margin_left = cell.margin_right = Inches(0.08)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            for p in cell.text_frame.paragraphs:
                for run in p.runs:
                    run.font.size, run.font.name = Pt(size), "Calibri"
                    run.font.bold = r == 0
                    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF) if r == 0 else INK
            cell.fill.solid()
            cell.fill.fore_color.rgb = header_fill if r == 0 else (PALE if r % 2 else RGBColor(0xFF, 0xFF, 0xFF))
    return shape


def picture(slide, path, x, y, w=None, h=None):
    return slide.shapes.add_picture(str(path), x, y, width=w, height=h)


def map_halves(name: str) -> list[dict]:
    import maps
    header = maps.POOL_X + maps.HEADER_W
    return [{"cols": (a, b), "title": t, "left": left, "right": right, "png": ROOT / "build" / f"{name}-slide-{i + 1}.png",
             "width_px": header + (b - a + 1) * maps.COL_W + maps.POOL_X}
            for i, (a, b, t, left, right) in enumerate(HALVES[name])]


def pct(v):
    return f"{v * 100:.0f}%"


def build(path: Path, assistant_excerpt: list[str], as_is, to_be) -> None:
    n = json.loads((ROOT / "build" / "numbers.json").read_text())
    risks = len(re.findall(r"^\| \d+ \|", (ROOT / "docs" / "change-risks.md").read_text(), re.M))
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H

    # 1 Title
    s = prs.slides.add_slide(prs.slide_layouts[6])
    band = s.shapes.add_shape(1, 0, 0, W, H)
    band.fill.solid(); band.fill.fore_color.rgb = INK; band.line.fill.background()
    text(s, Inches(0.9), Inches(1.6), Inches(11.5), Inches(0.5), "PORTFOLIO PIECE · CIB OPERATIONS · HONG KONG", size=14, color=RGBColor(0x8F, 0xB8, 0xF0), bold=True)
    text(s, Inches(0.9), Inches(2.2), Inches(11.5), Inches(2.0), "AI-first redesign of corporate client onboarding and periodic KYC review", size=40, color=RGBColor(0xFF, 0xFF, 0xFF), bold=True)
    text(s, Inches(0.9), Inches(4.3), Inches(11.2), Inches(1.2),
         "As-Is and To-Be BPMN maps with human approval gates and client moments of truth, a KPI model, a working "
         "assistant prototype, a rollout roadmap and a change-risk plan.", size=18, color=RGBColor(0xD5, 0xDB, 0xE3))
    text(s, Inches(0.9), Inches(6.2), Inches(11.5), Inches(0.8),
         [f"Eduard Rodriguez Lopez · {date(2026, 11, 18):%B %Y}",
          "Built from public material for a fictional CIB branch in Hong Kong. All KPI figures are simulated."],
         size=12, color=RGBColor(0xAE, 0xB6, 0xC2), space=2)

    # 2 Problem
    s = page(prs, "The problem: slow onboarding, and every extra ask shows", "Why this process",
             source="Thomson Reuters KYC surveys 2016 (older data); Fenergo financial crime trends 2025 (vendor survey, 600 firms, "
                    "global); HKMA circular on the risk-based approach to CDD, 8 Feb 2024; HKMA AML/CFT Guideline, May 2023, para 5.3.")
    bullets(s, Inches(0.6), Inches(1.8), Inches(12), Inches(4.8), [
        [("Clients feel it: ", True), ("in a 2016 survey, corporates reported about eight interactions with their bank per "
                                       "onboarding, and 30% said it took more than two months.", False)],
        [("Banks pay for it: ", True), ("in 2025, 70% of firms said they lost clients to inefficient onboarding in the past year, and about "
                                        "10% of applications are abandoned.", False)],
        [("The supervisor has said so: ", True), ("the HKMA asks banks not to request information they already hold or that is "
                                                   "publicly available.", False)],
        [("It repeats: ", True), ("periodic reviews redo much of the same work, at least yearly for high-risk clients.", False)],
        [("The opportunity: ", True), ("let AI do the reading and drafting, keep every decision with a person, and ask the "
                                       "client once.", False)],
    ], size=20)

    # 3 Scope and method
    s = page(prs, "Scope and method: one process, mapped end to end", "What was done")
    text(s, Inches(0.6), Inches(1.7), Inches(5.6), Inches(0.4), "In scope", size=18, bold=True)
    bullets(s, Inches(0.6), Inches(2.2), Inches(5.6), Inches(3.5), [
        "Onboarding a new corporate client, from first request to accounts live",
        "Periodic KYC review of an existing client, from review due to file current",
        "Roles: client, relationship manager, onboarding & KYC operations, compliance, systems",
        "Hong Kong rules; Singapore's differences noted for rollout",
    ], size=17)
    text(s, Inches(6.8), Inches(1.7), Inches(6), Inches(0.4), "Method", size=18, bold=True)
    bullets(s, Inches(6.8), Inches(2.2), Inches(6), Inches(3.6), [
        "Map today's process (As-Is) in BPMN, with pain points on the steps where they happen",
        "Redesign it (To-Be): AI steps that read and draft, a human approval gate before anything counts",
        "Simulate both maps on the same simulated cases to compare cycle time, touch time, first pass, rework and client touches",
        "Build the AI step as a working prototype; plan the rollout and its risks",
    ], size=17)
    text(s, Inches(0.6), Inches(6.0), Inches(12.2), Inches(0.6),
         "Built only from public rules and fictional examples. No real bank's process, client or data is used.",
         size=13, color=GREEN, bold=True)

    # 4-7 Maps, each in two readable halves
    for name, proc, kicker, title in (("as-is", as_is, "Today's process (BPMN)", "As-Is: generic requests, re-keying and late checks"),
                                      ("to-be", to_be, "The redesign (BPMN)", "To-Be: AI reads and drafts, people decide")):
        for k, half in enumerate(map_halves(name)):
            s = page(prs, f"{title} ({k + 1}/2)", f"{kicker}: {half['title']}",
                     footer=f"Full BPMN file, opens in bpmn.io or Camunda Modeler: deliverables/maps/{name}.bpmn",
                     footer_y=7.0)  # one footer line; the map legend needs the space above it
            a, b = half["cols"]
            on_half = {sid for sid, st in proc.steps.items() if a <= st["col"] <= b}
            if name == "as-is":
                notes = [[(f"{x['id']}  ", True), (x["text"], False)] for x in proc.pain_points if x["step"] in on_half]
                color = INK_2
            else:
                notes = [[("Dashed purple: ", True), ("AI steps; they read and draft, never decide.  ", False),
                          ("Bold green: ", True), ("human approval gates.  ", False), ("✓P: ", True), ("the As-Is pain removed.", False)]]
                color = INK_2
            moments = [[(f"{m['id']}  ", True), (m["text"], False)] for m in proc.moments if m["step"] in on_half]
            # Shrink the map so the legend (about 0.17 in per 11 pt line, the longest column wrapping to two
            # lines at most) ends above the footer at 6.85 in.
            legend_h = Inches(0.17) * max(len(notes), 2 * len(moments)) + Inches(0.1)
            max_h = min(Inches(4.75), Inches(6.85) - Inches(1.45) - Inches(0.12) - legend_h)
            pic = picture(s, half["png"], Inches(0.45), Inches(1.45), w=Inches(MAP_WIDTH_IN))
            if pic.height > max_h:
                ratio = max_h / pic.height
                pic.height, pic.width = int(max_h), int(pic.width * ratio)
                pic.left = int((W - pic.width) / 2)
            y = pic.top + pic.height + Inches(0.12)
            text(s, Inches(0.6), y, Inches(7.6), Inches(6.85) - y, notes, size=11, color=color, space=1)
            text(s, Inches(8.4), y, Inches(4.5), Inches(6.85) - y, moments, size=11, color=ORANGE, space=1)

    # 6 Gates
    s = page(prs, "Human approval gates: a person approves every AI output", "Control design",
             source="HKMA High-level Principles on AI, Nov 2019 (accountability, explainability, human-in-the-loop controls); "
                    "HKMA GenAI consumer-protection circular, Aug 2024 (human-in-the-loop for customer-facing use).")
    table(s, Inches(0.6), Inches(1.7), Inches(12.1), [
        ["AI step", "What it produces", "Approved by, before it counts"],
        ["Pre-fill from registries and the file", "A tailored list of only what is missing", "Analyst approves the one client request"],
        ["Read the pack", "Extracted facts, each with the exact words it came from", "Analyst reviews the draft and its flags"],
        ["Triage screening hits", "An explanation for each possible match", "Analyst decides each hit"],
        ["(Rules, not AI) Risk rating", "A proposed rating with its reasons", "Analyst confirms and records it"],
        ["Draft the EDD memo", "A memo with sources", "Compliance reviews and decides; senior approval stays"],
        ["Pre-QC", "A list of file defects", "QC sign-off"],
    ], [0.3, 0.37, 0.33], size=13, row_h=0.55)
    text(s, Inches(0.6), Inches(5.75), Inches(12.1), Inches(0.9),
         "The rule is checked by script on the To-Be model: no path from an AI step reaches the client, the rating or the "
         "file without passing a human gate. A client can always reach a person.", size=14, color=INK_2)

    # 7 Moments of truth
    s = page(prs, "Moments of truth: three points where the client judges the bank", "Client journey")
    table(s, Inches(0.6), Inches(1.7), Inches(12.1), [
        ["Moment", "As-Is", "To-Be"],
        ["M1  First request", "A generic checklist by email; unclear what applies", "One tailored list; one upload in the portal"],
        ["M2  Being asked again", "Chased in rounds for missing items", "At most one follow-up with every item; none on a review with nothing missing"],
        ["M3  Accounts live", "Weeks of waiting, mostly in queues", "Days sooner, with fewer asks on the way"],
    ], [0.22, 0.39, 0.39], size=14, row_h=0.75)
    text(s, Inches(0.6), Inches(5.2), Inches(12.1), Inches(1.2),
         "Each moment gets a one-question client pulse in the pilot, so the redesign is judged from the client's side, "
         "not only by internal KPIs.", size=15, color=INK_2)

    # 8 KPIs onboarding
    s = page(prs, "KPIs, onboarding: shorter, fewer loops, fewer asks", "Simulated model", footer=SIM + " " + TOUCHES)
    picture(s, ROOT / "deliverables" / "charts" / "kpi-onboarding.png", Inches(0.9), Inches(1.45), w=Inches(11.4))
    text(s, Inches(0.6), Inches(6.45), Inches(12.2), Inches(0.4),
         f"Sensitivity: if every human step kept today's queue time, To-Be onboarding would take {n['onb_cycle_days_to_be_slow_queues']:.1f} "
         f"days instead of {n['onb_cycle_days_to_be']:.1f} (As-Is {n['onb_cycle_days_as_is']:.1f}).", size=13, color=INK_2)

    # 9 KPIs review
    s = page(prs, "KPIs, periodic review: most of the gain is not asking again", "Simulated model", footer=SIM + " " + TOUCHES)
    picture(s, ROOT / "deliverables" / "charts" / "kpi-review.png", Inches(0.9), Inches(1.45), w=Inches(11.4))
    text(s, Inches(0.6), Inches(6.45), Inches(12.2), Inches(0.4),
         f"About {n['fte_saved']:.1f} full-time staff a year freed across both, to move to enhanced due diligence and backlog. "
         f"With today's queues, a To-Be review takes {n['rev_cycle_days_to_be_slow_queues']:.1f} days instead of {n['rev_cycle_days_to_be']:.1f}.",
         size=13, color=INK_2)

    # 10 Assistant
    s = page(prs, "The assistant: a working prototype of the AI step", "What was built",
             footer="Run on a fictional sample pack, offline. Code, tests and samples: assistant/. A Gemini Gem version: deliverables/gem/.")
    bullets(s, Inches(0.6), Inches(1.7), Inches(5.4), Inches(4.8), [
        "The model only extracts facts, each with its exact source words",
        "A fact counts only if its quote is in the document and contains the claimed value",
        "Fixed rules decide: beneficial owners through every chain, missing documents, changes since the last review",
        "Every missing item goes into one client request",
        "Nothing leaves until an analyst ticks approve (or edits) in a separate release step",
    ], size=15)
    box = s.shapes.add_shape(1, Inches(6.3), Inches(1.7), Inches(6.45), Inches(4.9))
    box.fill.solid(); box.fill.fore_color.rgb = PALE; box.line.color.rgb = LINE
    text(s, Inches(6.5), Inches(1.8), Inches(6.1), Inches(4.7), assistant_excerpt, size=11, color=INK, font="Courier New", space=2)

    # 11 Roadmap
    s = page(prs, "Roadmap: four phases, each opened by a measured gate", "Implementation",
             source="HKMA RBA-CDD circular, Feb 2024 (no duplicate requests); HKMA speech on its 2026 AI guidance, 16 Oct 2026 (owner and inventory per AI use).")
    phases = [("Phase 0", "Weeks 0–6", "Measure the real As-Is; agree KPI definitions and the gates with compliance; register the AI use",
               "Baseline signed off; gates agreed in writing"),
              ("Phase 1", "Weeks 6–16", "Shadow, then assist, on low- and medium-risk periodic reviews; nothing client-facing",
               "Extraction accuracy target met; no ungated output; touch time down"),
              ("Phase 2", "Months 4–8", "Onboarding with one tailored request and one upload; screening-hit triage",
               "Cycle time and first pass better; client pulse no worse"),
              ("Phase 3", "Months 8–12", "EDD memo drafts, pre-QC, event-driven reviews; Singapore rules configuration",
               "Reviews on time up; no rise in QC or regulatory findings")]
    for i, (name, when, ships, gate) in enumerate(phases):
        x = Inches(0.6 + i * 3.08)
        card = s.shapes.add_shape(1, x, Inches(1.7), Inches(2.9), Inches(4.9))
        card.fill.solid(); card.fill.fore_color.rgb = PALE; card.line.color.rgb = LINE
        text(s, x + Inches(0.15), Inches(1.8), Inches(2.6), Inches(0.5), [[(name + "  ", True), (when, False)]], size=15, color=BLUE)
        text(s, x + Inches(0.15), Inches(2.35), Inches(2.6), Inches(2.4), ships, size=13, color=INK_2)
        text(s, x + Inches(0.15), Inches(4.7), Inches(2.6), Inches(1.8), [[("Gate: ", True), (gate, False)]], size=12, color=GREEN)

    # 12 Risks
    s = page(prs, "Change risks: the five that could cause a regulatory finding", "Change management",
             source=f"HKMA High-level Principles on AI, Nov 2019; AMLO (Cap. 615) Schedule 2. Full register ({risks} risks): deliverables/docs/change-risks.docx")
    table(s, Inches(0.6), Inches(1.7), Inches(12.1), [
        ["Risk", "L / I", "Mitigation", "Early signal"],
        ["Analysts approve AI drafts without checking (automation bias)", "H / H", "Source words on every fact; planted-error test packs; QC samples approved drafts", "Approval time collapses; planted errors pass"],
        ["A wrong extracted fact reaches the file", "M / H", "Quote-and-value verification; human approval of every change; pre-QC", "QC defects above baseline"],
        ["Complex structures (trusts, nominees, control) treated as simple", "M / H", "Rules say what they can't see; manual path for those cases", "QC finds a missed beneficial owner"],
        ["Supervisor sees a black box", "L / H", "Gates, explanations and the bank's audit trail; a named owner and inventory entry for the AI use", "Questions the audit trail can't answer"],
        ["KPIs reward speed over quality", "M / M", "First pass and QC defects reported next to cycle time", "Cycle time down while rework rises"],
    ], [0.3, 0.08, 0.36, 0.26], size=12, row_h=0.7)

    # 13 Sources
    s = page(prs, "Sources and notes", "Where every fact comes from",
             source="each item below; URLs, exact quotes and access dates are in the project's sources/ folder.")
    text(s, Inches(0.6), Inches(1.6), Inches(7.4), Inches(5.2), [
        [("Rules  ", True), ("AMLO (Cap. 615) Schedule 2 · HKMA Guideline on AML/CFT (May 2023) · HKMA circular on the "
                             "risk-based approach to CDD (Feb 2024) · Companies Registry, Significant Controllers Register · "
                             "MAS Notice 626 and its Guidelines", False)],
        [("AI supervision  ", True), ("HKMA High-level Principles on AI (Nov 2019) · HKMA GenAI consumer-protection circular "
                                      "(Aug 2024) · HKMA GenAI Sandbox cohorts · HKMA speech on its 2026 AI guidance (Oct 2026)", False)],
        [("Benchmarks  ", True), ("Thomson Reuters KYC surveys (2016, 2017) · Fenergo KYC and financial crime trend "
                                  "reports (2023–2025). Vendor surveys, self-reported, none sampled in Hong Kong.", False)],
        [("Standard  ", True), ("OMG BPMN 2.0.2", False)],
    ], size=13, color=INK_2, space=12)
    text(s, Inches(8.4), Inches(1.6), Inches(4.4), Inches(5.2), [
        [("What is simulated  ", True), ("Every KPI figure. The model walks simulated cases through both maps; every input "
                                         "is a labelled guess in the workbook's Assumptions tab, to be replaced by measured "
                                         "times in Phase 0.", False)],
        [("What is fictional  ", True), ("The bank, its branch, and every company and person in the assistant's samples.", False)],
        [("Everything else  ", True), ("Linked with URL, exact quote and access date in sources/ of the project.", False)],
    ], size=13, color=INK_2, space=12)

    path.parent.mkdir(parents=True, exist_ok=True)
    prs.core_properties.author = "Eduard Rodriguez Lopez"
    prs.core_properties.title = "AI-first redesign of CIB client onboarding and periodic KYC review"
    prs.save(path)
