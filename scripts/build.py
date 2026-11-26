"""Regenerate every generated artifact from the model files. `make build` runs this.

Implements: process-maps/one-source, process-maps/pictures, kpi-model/numbers-from-model, kpi-model/sheets-ready, package/roadmap, package/change-risks, package/access-guide, package/readable-tables, kpi-model/assumptions-justified, package/deck

Each stage is a function; later items add theirs to STAGES. Everything written here is reproducible from the
committed model files, so a reader can delete deliverables/ and get identical files back.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import charts  # noqa: E402
import maps  # noqa: E402
import yaml  # noqa: E402
import score_live  # noqa: E402
import simulate  # noqa: E402
import workbook  # noqa: E402

SIMULATED = "Illustrative redesign for a CIB branch in Hong Kong. Built from public material; simulated, not real bank data."


def build_maps() -> None:
    out = ROOT / "deliverables" / "maps"
    out.mkdir(parents=True, exist_ok=True)
    pains = maps.load(ROOT / "model" / "as-is.yaml").pain_points
    for name in ("as-is", "to-be"):
        proc = maps.load(ROOT / "model" / f"{name}.yaml")
        problems = maps.problems(proc)
        if problems:
            raise SystemExit(f"{name}.yaml: " + "; ".join(problems))
        (out / f"{name}.bpmn").write_text(maps.bpmn_xml(proc), encoding="utf-8")
        (out / f"{name}.svg").write_text(maps.svg(proc, SIMULATED, pains), encoding="utf-8")
        subprocess.run(["rsvg-convert", "-z", "1", "-o", str(out / f"{name}.png"), str(out / f"{name}.svg")], check=True)
        import deck
        full_lane = maps.LANE_H
        maps.LANE_H = 120  # slide view: shorter lanes, so the map fills the slide at a readable size
        for half in deck.map_halves(name):  # two readable halves of the map, for the deck
            half["png"].parent.mkdir(exist_ok=True)
            cut = half["png"].with_suffix(".svg")
            cut.write_text(maps.svg_slice(proc, *half["cols"], half["left"], half["right"]), encoding="utf-8")
            subprocess.run(["rsvg-convert", "-z", "2", "-o", str(half["png"]), str(cut)], check=True)
        maps.LANE_H = full_lane
        print(f"maps: {name}.bpmn, .svg, .png")


def build_model() -> None:
    """Simulate both maps, write build/numbers.json (what every other file quotes), the workbook and the charts."""
    result = simulate.run()
    (ROOT / "build").mkdir(exist_ok=True)
    live = score_live.numbers()  # live model runs, scored against the hand-written replies
    (ROOT / "assistant" / "live" / "results.md").write_text(score_live.render(), encoding="utf-8")
    (ROOT / "build" / "numbers.json").write_text(json.dumps({**result.numbers, **live}, indent=1) + "\n", encoding="utf-8")
    workbook.write(result.cases, result.numbers, ROOT / "deliverables" / "kpi-model.xlsx")
    charts.figure(result.numbers, "onb", "Onboarding a corporate client: As-Is vs To-Be", ROOT / "deliverables" / "charts" / "kpi-onboarding.png")
    charts.figure(result.numbers, "rev", "Periodic KYC review: As-Is vs To-Be", ROOT / "deliverables" / "charts" / "kpi-review.png")
    print(f"model: {len(result.cases)} simulated cases, {len(result.numbers)} numbers, workbook, 2 charts")


CITE = re.compile(r"\s*\[src:([a-z0-9-]+)\]")
MARKER = re.compile(r"<!--\s*check:[^>]*-->")


def sources() -> dict[str, dict]:
    return {e["key"]: e for path in sorted((ROOT / "sources").glob("*.yaml"))
            for e in yaml.safe_load(path.read_text(encoding="utf-8"))}


def cited(path: Path) -> list[str]:
    """Source keys a Markdown file cites, in order of first use."""
    return list(dict.fromkeys(CITE.findall(path.read_text(encoding="utf-8"))))


def for_readers(text: str, known: dict[str, dict]) -> str:
    """Markdown as a reader should see it: check markers removed, `[src:key]` turned into numbered references,
    and a Sources list at the end with each source's publisher, title, date and link."""
    order: list[str] = []

    def number(m: re.Match) -> str:
        if m.group(1) not in order:
            order.append(m.group(1))
        return f" [{order.index(m.group(1)) + 1}]"

    body = CITE.sub(number, MARKER.sub("", text))
    body = re.sub(r"\] \[", "][", body)
    if order:
        body += "\n\n## Sources\n\n" + "\n".join(
            f"{i}. {known[k].get('publisher', '')}, *{known[k]['title']}* ({known[k].get('date_published', 'undated')}). <{known[k]['url']}>"
            for i, k in enumerate(order, 1)) + "\n"
    return body


def pin_zip(path: Path) -> None:
    """Make an Office file reproducible: fixed dates in its properties and its zip entries."""
    import zipfile
    with zipfile.ZipFile(path) as z:
        parts = [(i.filename, z.read(i.filename)) for i in z.infolist()]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in parts:
            if name == "docProps/core.xml":
                data = re.sub(rb"(<dcterms:(?:created|modified)[^>]*>)[^<]*(</dcterms:)", rb"\g<1>2026-11-18T00:00:00Z\g<2>", data)
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 18, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)


PUBLIC_DOCS = ("roadmap", "change-risks", "access-guide", "assumptions")  # the Google Docs deliverables; the other docs/ files are how-tos for the owner

A4 = (11906, 16838)  # page width and height in twentieths of a point
MARGIN = 1134  # 2 cm
TABLE_BORDERS = ("<w:tblBorders>" + "".join(f'<w:{side} w:val="single" w:sz="4" w:space="0" w:color="BFC6D1" />'
                 for side in ("top", "left", "bottom", "right", "insideH", "insideV")) + "</w:tblBorders>")
CELL_MARGINS = ('<w:tblCellMar><w:top w:w="57" w:type="dxa" /><w:left w:w="85" w:type="dxa" />'
                '<w:bottom w:w="57" w:type="dxa" /><w:right w:w="85" w:type="dxa" /></w:tblCellMar>')


def readable_tables(xml: str) -> str:
    """Pandoc's tables arrive borderless and cramped, which Google Docs shows as a wall of text. Give each table
    borders, a shaded bold header, smaller text and columns that fill the page in the Markdown's proportions; turn
    the page to landscape when a table has more than six columns."""
    wide = any(len(re.findall(r"<w:gridCol ", t)) > 6 for t in re.findall(r"<w:tbl>.*?</w:tbl>", xml, re.S))
    width, height = (A4[1], A4[0]) if wide else A4
    text_width = width - 2 * MARGIN

    def table(m: re.Match) -> str:
        t = m.group(0)
        t = t.replace("<w:tblLayout ", TABLE_BORDERS + "<w:tblLayout ", 1)
        t = re.sub(r"(<w:tblLayout [^>]*/>)", r"\1" + CELL_MARGINS, t, count=1)
        cols = [int(w) for w in re.findall(r'<w:gridCol w:w="(\d+)"', t)]
        sized = [round(text_width * c / sum(cols)) for c in cols]
        sized[-1] += text_width - sum(sized)
        grid = "".join(f'<w:gridCol w:w="{w}" />' for w in sized)
        t = re.sub(r"<w:tblGrid>.*?</w:tblGrid>", f"<w:tblGrid>{grid}</w:tblGrid>", t, count=1, flags=re.S)
        t = re.sub(r"<w:r>(?!<w:rPr>)", '<w:r><w:rPr><w:sz w:val="18" /><w:szCs w:val="18" /></w:rPr>', t)
        t = re.sub(r"(<w:r><w:rPr>(?:(?!</w:rPr>).)*?)</w:rPr>",
                   lambda r: r.group(0) if "<w:sz " in r.group(1) else r.group(1) + '<w:sz w:val="18" /><w:szCs w:val="18" /></w:rPr>', t)
        head_end = t.index("</w:tr>")
        head = t[:head_end].replace("<w:tcPr />", '<w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="E3EAF3" /></w:tcPr>')
        head = head.replace('<w:rPr><w:sz w:val="18" />', '<w:rPr><w:b /><w:bCs /><w:sz w:val="18" />')
        return head + t[head_end:]

    xml = re.sub(r"<w:tbl>.*?</w:tbl>", table, xml, flags=re.S)
    orient = ' w:orient="landscape"' if wide else ""
    page = (f'<w:pgSz w:w="{width}" w:h="{height}"{orient} />'
            f'<w:pgMar w:top="{MARGIN}" w:right="{MARGIN}" w:bottom="{MARGIN}" w:left="{MARGIN}" w:header="567" '
            f'w:footer="567" w:gutter="0" />')
    return re.sub(r"(</w:footnotePr>\s*)(</w:sectPr>)", r"\g<1>" + page + r"\2", xml, count=1)


ASSUMPTION_STEPS = "<!-- assumption steps -->"
MAPS = {"as_is": "As-Is map", "to_be": "To-Be map"}


def assumption_steps() -> str:
    """The step-by-step part of docs/assumptions.md: each input's value read from model/assumptions.yaml, next to
    the reason in model/assumption-reasons.yaml, grouped by the step on the map that uses it."""
    values = {k: v for group in yaml.safe_load((ROOT / "model" / "assumptions.yaml").read_text()).values()
              for k, v in group.items()}
    reasons = yaml.safe_load((ROOT / "model" / "assumption-reasons.yaml").read_text())

    def show(key: str, plain: bool = False) -> str:
        v, unit = values[key]["value"], values[key]["unit"]
        if plain and unit == "days":
            return f"{v:g} days"
        if isinstance(v, dict):
            return ", ".join(f"{t} {x:.0%}" for t, x in v.items())
        if unit == "share":
            return f"{v:.0%}"
        if unit == "hours":
            return f"{v:g} h hands-on"
        if unit == "days":
            return f"{v:g} days elapsed"
        if isinstance(v, list):
            return f"{v[0]:g}x to {v[1]:g}x the typical value"
        return f"{v:g} {unit}" if unit != "-" else f"{v:g}"

    def entry(title: str, keys: list[str], reason: dict, plain: bool = False) -> str:
        cites = "".join(f" [src:{k}]" for k in reason.get("src", []))
        return (f"#### {title}\n\n- **Input:** {'; '.join(show(k, plain) for k in keys)} (Assumptions tab: "
                f"{', '.join(f'`{k}`' for k in keys)})\n- **Why:** {reason['why']}{cites}\n")

    out = ["### Run settings\n"]
    for key, reason in reasons["run"].items():
        out.append(entry(reason["title"], [key], reason, plain=True))
    out.append("### Shares used on both maps\n")
    for key, reason in reasons["shared"].items():
        out.append(entry(reason["title"], [key], reason, plain=True))
    for side, heading in MAPS.items():
        m = yaml.safe_load((ROOT / "model" / f"{side.replace('_', '-')}.yaml").read_text())
        lanes = {lane["id"]: lane["name"] for lane in m["lanes"]}
        out.append(f"### {heading}\n")
        for step in m["steps"]:
            if step["type"] == "gateway":
                flows = [f for f in m["flows"] if isinstance(f, dict) and f.get("from") == step["id"] and "p" in f]
                keys = [f["p"] for f in flows if f["p"] in values and not f["p"] in reasons["shared"]]
                title = f"{step['label']} (share answered \"{flows[0]['label']}\")" if flows else ""
            else:
                keys = [step[k] for k in ("touch", "wait") if k in step]
                title = f"{step['label']} ({lanes[step['lane']]})"
            if keys:
                out.append(entry(title, keys, reasons[side][step["id"]]))
    return "\n".join(out)


def build_docs(out: Path | None = None) -> None:
    """docs/*.md to Word files for Google Docs (deliverables/docs/), readable: no markers, numbered sources,
    tables that survive the conversion."""
    import zipfile
    out = out or ROOT / "deliverables" / "docs"
    out.mkdir(parents=True, exist_ok=True)
    known = sources()
    for md in (ROOT / "docs" / f"{name}.md" for name in PUBLIC_DOCS):
        text = md.read_text(encoding="utf-8").replace(ASSUMPTION_STEPS, assumption_steps())
        text = for_readers(text, known)
        path = out / f"{md.stem}.docx"
        subprocess.run(["pandoc", "--from", "markdown", "--to", "docx", "-o", str(path)], input=text.encode(), check=True)
        with zipfile.ZipFile(path) as z:
            parts = [(i.filename, z.read(i.filename)) for i in z.infolist()]
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in parts:
                z.writestr(name, readable_tables(data.decode()).encode() if name == "word/document.xml" else data)
        pin_zip(path)
        print(f"docs: {md.stem}.docx")


def draft_image(result, path: Path) -> None:
    """The assistant's draft review as an image for the site: flags and the client request, in a monospace card."""
    from xml.sax.saxutils import escape
    import textwrap
    lines = ["DRAFT KYC ONBOARDING REVIEW (fictional sample), awaiting analyst approval", ""]
    lines += ["Beneficial owners: " + "; ".join(f"{o.name} {o.percent:.0f}%" for o in result.beneficial_owners), "", "Flags:"]
    lines += [w for f in result.flags for w in textwrap.wrap(f"- {f.reason}", 92, subsequent_indent="  ")]
    lines += ["", "Client request (one message):"]
    lines += [w for ln in result.client_request.splitlines() for w in (textwrap.wrap(ln, 92, subsequent_indent="   ") or [""])]
    lines += ["", "[ ] Approve as drafted   [ ] Edit, then approve   [ ] Reject"]
    h = 40 + 19 * len(lines)
    body = "".join(f'<text x="24" y="{36 + 19 * i}">{escape(t)}</text>' for i, t in enumerate(lines))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{h}"><rect width="100%" height="100%" rx="10" '
           f'fill="#f3f5f8" stroke="#d9dee5"/><g font-family="DejaVu Sans Mono, Courier New, monospace" font-size="13" '
           f'fill="#161b24">{body}</g></svg>')
    path.parent.mkdir(parents=True, exist_ok=True)
    src = ROOT / "build" / "draft.svg"
    src.write_text(svg, encoding="utf-8")
    subprocess.run(["rsvg-convert", "-z", "1.5", "-o", str(path), str(src)], check=True)


def build_deck() -> None:
    """The deck, with a live excerpt of the assistant's draft on a fictional sample pack."""
    import textwrap
    from datetime import date

    import deck
    sys.path.insert(0, str(ROOT))
    from assistant import llm, rules

    pack = ROOT / "assistant" / "samples" / "harbour-lantern"
    result = rules.evaluate(pack, llm.replay(pack), date(2026, 11, 18))
    lines = result.client_request.splitlines()
    items = [ln for ln in lines if ln[:2].rstrip(".").isdigit()]
    excerpt = ["DRAFT, awaiting analyst approval", f"{len(result.flags)} flags; beneficial owners: "
               + ", ".join(o.name for o in result.beneficial_owners), "", lines[0], ""]
    for item in items[:5]:
        excerpt += textwrap.wrap(item, 56, subsequent_indent="   ")
    excerpt += [f"   ... and {len(items) - 5} more" if len(items) > 5 else "", "", "[ ] Approve  [ ] Edit, then approve  [ ] Reject"]
    as_is, to_be = maps.load(ROOT / "model" / "as-is.yaml"), maps.load(ROOT / "model" / "to-be.yaml")
    draft_image(result, ROOT / "deliverables" / "assistant" / "draft-harbour-lantern.png")
    deck.build(ROOT / "deliverables" / "deck.pptx", excerpt, as_is, to_be)
    pin_zip(ROOT / "deliverables" / "deck.pptx")
    print("deck: deck.pptx")


STAGES = [build_maps, build_model, build_docs, build_deck]


if __name__ == "__main__":
    for stage in STAGES:
        stage()
