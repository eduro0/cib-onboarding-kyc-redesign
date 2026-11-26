"""Process files (model/*.yaml) to BPMN 2.0 XML with diagram layout, and to an SVG picture of the same layout.

Implements: process-maps/as-is-map, process-maps/to-be-map, process-maps/one-source, process-maps/opens-in-bpmn-io, process-maps/pictures, process-maps/human-gates, process-maps/pain-points, process-maps/moments-of-truth

One process file is the single source for a map: lanes, steps (each with a lane and a column), flows, pain points
and moments of truth. `layout()` places every step on a grid (column × lane) and routes every flow as right-angled
waypoints; `bpmn_xml()` and `svg()` both draw from that one layout, so the BPMN tool and the slide show the same
picture. `problems()` holds the structural checks, including the human-gate rule for To-Be maps.
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape

import yaml

COL_W, LANE_H, HEADER_W, POOL_X, POOL_Y = 150, 150, 40, 20, 20
TASK_W, TASK_H, GW, EV = 122, 78, 46, 36
STEP_TYPES = {"start", "timer", "end", "task", "client", "ai", "system", "gateway"}
BPMN_TAG = {"start": "startEvent", "timer": "startEvent", "end": "endEvent", "task": "userTask", "client": "task",
            "ai": "serviceTask", "system": "serviceTask", "gateway": "exclusiveGateway"}


@dataclass
class Process:
    id: str
    title: str
    lanes: list[dict]
    steps: dict[str, dict]
    flows: list[dict]
    pain_points: list[dict] = field(default_factory=list)
    moments: list[dict] = field(default_factory=list)


def load(path: Path) -> Process:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    flows = []
    for i, f in enumerate(raw["flows"]):
        f = {"from": f[0], "to": f[1]} if isinstance(f, list) else dict(f)
        f["id"] = f"flow_{i + 1}"
        flows.append(f)
    return Process(raw["id"], raw["title"], raw["lanes"], {s["id"]: s for s in raw["steps"]}, flows,
                   raw.get("pain_points", []), raw.get("moments_of_truth", []))


def problems(p: Process) -> list[str]:
    """Structural problems: unknown references, unreachable steps, dead ends, clashing cells, ungated AI effects."""
    out: list[str] = []
    lanes = {lane["id"] for lane in p.lanes}
    cells: dict[tuple, str] = {}
    for s in p.steps.values():
        if s["type"] not in STEP_TYPES:
            out.append(f"{s['id']}: unknown type {s['type']}")
        if s["lane"] not in lanes:
            out.append(f"{s['id']}: unknown lane {s['lane']}")
        cell = (s["lane"], s["col"])
        if cell in cells:
            out.append(f"{s['id']}: same cell as {cells[cell]}")
        cells[cell] = s["id"]
    nxt: dict[str, list[str]] = {sid: [] for sid in p.steps}
    incoming: dict[str, int] = {sid: 0 for sid in p.steps}
    for f in p.flows:
        for end in ("from", "to"):
            if f[end] not in p.steps:
                out.append(f"{f['id']}: unknown step {f[end]}")
        if f["from"] in p.steps and f["to"] in p.steps:
            nxt[f["from"]].append(f["to"])
            incoming[f["to"]] += 1
    starts = [s for s in p.steps.values() if s["type"] in {"start", "timer"}]
    seen, todo = set(), [s["id"] for s in starts]
    while todo:
        sid = todo.pop()
        if sid not in seen:
            seen.add(sid)
            todo.extend(nxt[sid])
    for sid, s in p.steps.items():
        if sid not in seen:
            out.append(f"{sid}: can't be reached from a start event")
        if s["type"] != "end" and not nxt[sid]:
            out.append(f"{sid}: has no outgoing flow")
        if s["type"] not in {"start", "timer"} and not incoming[sid]:
            out.append(f"{sid}: has no incoming flow")
    for ref in p.pain_points + p.moments:
        if ref["step"] not in p.steps:
            out.append(f"{ref['id']}: on unknown step {ref['step']}")
    out += ungated_ai_effects(p, nxt)
    return out


def ungated_ai_effects(p: Process, nxt: dict[str, list[str]] | None = None) -> list[str]:
    """Every path from an AI step to a step that changes the client, the rating or the file must pass a gate."""
    if nxt is None:
        nxt = {sid: [f["to"] for f in p.flows if f["from"] == sid] for sid in p.steps}
    out = []
    for sid, s in p.steps.items():
        if s["type"] != "ai":
            continue
        seen, todo = set(), list(nxt.get(sid, []))
        while todo:
            cur = todo.pop()
            if cur in seen or cur not in p.steps:
                continue
            seen.add(cur)
            step = p.steps[cur]
            if step.get("gate"):
                continue
            if step.get("effect"):
                out.append(f"{sid}: AI output reaches '{cur}' without a human gate")
                continue
            todo.extend(nxt.get(cur, []))
    return out


def lane_y(p: Process, lane: str) -> int:
    return POOL_Y + [lane_["id"] for lane_ in p.lanes].index(lane) * LANE_H


def box(p: Process, s: dict) -> tuple[int, int, int, int]:
    """(x, y, w, h) of a step's shape."""
    cx = POOL_X + HEADER_W + s["col"] * COL_W + COL_W // 2
    cy = lane_y(p, s["lane"]) + LANE_H // 2
    w, h = {"gateway": (GW, GW), "start": (EV, EV), "timer": (EV, EV), "end": (EV, EV)}.get(s["type"], (TASK_W, TASK_H))
    return cx - w // 2, cy - h // 2, w, h


def size(p: Process) -> tuple[int, int]:
    cols = max(s["col"] for s in p.steps.values()) + 1
    return HEADER_W + cols * COL_W, len(p.lanes) * LANE_H


def route(p: Process, f: dict, channel: int) -> list[tuple[int, int]]:
    """Right-angled waypoints for one flow. Back edges in one lane run in a channel above or below the shapes."""
    a, b = p.steps[f["from"]], p.steps[f["to"]]
    ax, ay, aw, ah = box(p, a)
    bx, by, bw, bh = box(p, b)
    acx, acy, bcx, bcy = ax + aw // 2, ay + ah // 2, bx + bw // 2, by + bh // 2
    if b["col"] > a["col"] and f.get("route") == "turn-first":  # leave vertically, then run along the target lane
        down = by > ay
        return [(acx, ay + ah if down else ay), (acx, bcy), (bx, bcy)]
    if b["col"] > a["col"] and f.get("route") == "below":  # forward, but under the shapes in the source lane
        y = lane_y(p, a["lane"]) + LANE_H - 12 - channel * 8
        turn = POOL_X + HEADER_W + b["col"] * COL_W - 6
        return [(acx, ay + ah), (acx, y), (turn, y), (turn, bcy), (bx, bcy)]
    if b["col"] > a["col"]:
        if a["lane"] == b["lane"]:
            return [(ax + aw, acy), (bx, bcy)]
        mid = POOL_X + HEADER_W + b["col"] * COL_W - 6 if b["col"] - a["col"] > 1 else (ax + aw + bx) // 2
        return [(ax + aw, acy), (mid, acy), (mid, bcy), (bx, bcy)]
    if b["col"] == a["col"]:
        down = by > ay
        return [(acx, ay + ah if down else ay), (bcx, by if down else by + bh)]
    if a["lane"] != b["lane"]:
        below = lane_y(p, b["lane"]) > lane_y(p, a["lane"])
        return [(ax, acy), (bcx, acy), (bcx, by if below else by + bh)]
    lane_top = lane_y(p, a["lane"])
    if f.get("route", "above") == "above":
        y = lane_top + 12 + channel * 8
        return [(acx, ay), (acx, y), (bcx, y), (bcx, by)]
    y = lane_top + LANE_H - 12 - channel * 8
    return [(acx, ay + ah), (acx, y), (bcx, y), (bcx, by + bh)]


def layout(p: Process) -> dict[str, list[tuple[int, int]]]:
    channels: dict[tuple, int] = {}
    paths = {}
    for f in p.flows:
        a, b = p.steps[f["from"]], p.steps[f["to"]]
        backward = b["col"] < a["col"] and a["lane"] == b["lane"]
        key = (a["lane"], f.get("route", "above")) if backward or f.get("route") == "below" else None
        n = channels.get(key, 0) if key else 0
        paths[f["id"]] = route(p, f, n)
        if key:
            channels[key] = n + 1
    return paths


def bpmn_xml(p: Process) -> str:
    """BPMN 2.0 XML: one pool with a lane per role, every step and flow, annotations, and full diagram layout."""
    paths = layout(p)
    width, height = size(p)
    outgoing = {sid: [f["id"] for f in p.flows if f["from"] == sid] for sid in p.steps}
    incoming = {sid: [f["id"] for f in p.flows if f["to"] == sid] for sid in p.steps}
    notes = [(f"{n['id']}: {n['text']}", n["step"], n["id"]) for n in p.pain_points + p.moments]
    for s in p.steps.values():
        if s.get("fixes"):
            notes.append((f"Fixes {', '.join(s['fixes'])}", s["id"], f"fix_{s['id']}"))
    x = [f'<?xml version="1.0" encoding="UTF-8"?>',
         f'<!-- Generated by scripts/maps.py from model/{p.id.replace("_", "-")}.yaml. Simulated example, not real bank data. -->',
         '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
         'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
         'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" '
         f'id="defs_{p.id}" targetNamespace="https://example.org/kyc-redesign" exporter="scripts/maps.py">',
         f'  <bpmn:collaboration id="collab_{p.id}">',
         f'    <bpmn:participant id="pool_{p.id}" name="{escape(p.title)}" processRef="proc_{p.id}" />',
         '  </bpmn:collaboration>',
         f'  <bpmn:process id="proc_{p.id}" isExecutable="false">',
         f'    <bpmn:laneSet id="lanes_{p.id}">']
    for lane in p.lanes:
        x.append(f'      <bpmn:lane id="lane_{lane["id"]}" name="{escape(lane["name"])}">')
        x += [f'        <bpmn:flowNodeRef>{sid}</bpmn:flowNodeRef>' for sid, s in p.steps.items() if s["lane"] == lane["id"]]
        x.append('      </bpmn:lane>')
    x.append('    </bpmn:laneSet>')
    for sid, s in p.steps.items():
        tag = BPMN_TAG[s["type"]]
        name = ("AI: " if s["type"] == "ai" else "") + s["label"]
        x.append(f'    <bpmn:{tag} id="{sid}" name="{escape(name)}">')
        if s.get("gate"):
            x.append('      <bpmn:documentation>Human approval gate: nothing passes without this decision.</bpmn:documentation>')
        x += [f'      <bpmn:incoming>{i}</bpmn:incoming>' for i in incoming[sid]]
        x += [f'      <bpmn:outgoing>{o}</bpmn:outgoing>' for o in outgoing[sid]]
        if s["type"] == "timer":
            x.append(f'      <bpmn:timerEventDefinition id="timer_{sid}" />')
        x.append(f'    </bpmn:{tag}>')
    for f in p.flows:
        label = f' name="{escape(f["label"])}"' if f.get("label") else ""
        x.append(f'    <bpmn:sequenceFlow id="{f["id"]}" sourceRef="{f["from"]}" targetRef="{f["to"]}"{label} />')
    for i, (text, _, nid) in enumerate(notes):
        x.append(f'    <bpmn:textAnnotation id="note_{nid}"><bpmn:text>{escape(text)}</bpmn:text></bpmn:textAnnotation>')
        x.append(f'    <bpmn:association id="assoc_{nid}" sourceRef="{notes[i][1]}" targetRef="note_{nid}" />')
    x.append('  </bpmn:process>')
    x.append(f'  <bpmndi:BPMNDiagram id="diagram_{p.id}">')
    x.append(f'    <bpmndi:BPMNPlane id="plane_{p.id}" bpmnElement="collab_{p.id}">')
    x.append(f'      <bpmndi:BPMNShape id="pool_{p.id}_di" bpmnElement="pool_{p.id}" isHorizontal="true">'
             f'<dc:Bounds x="{POOL_X}" y="{POOL_Y}" width="{width}" height="{height}" /></bpmndi:BPMNShape>')
    for lane in p.lanes:
        x.append(f'      <bpmndi:BPMNShape id="lane_{lane["id"]}_di" bpmnElement="lane_{lane["id"]}" isHorizontal="true">'
                 f'<dc:Bounds x="{POOL_X + 30}" y="{lane_y(p, lane["id"])}" width="{width - 30}" height="{LANE_H}" /></bpmndi:BPMNShape>')
    for sid, s in p.steps.items():
        bx, by, bw, bh = box(p, s)
        marker = ' isMarkerVisible="true"' if s["type"] == "gateway" else ""
        x.append(f'      <bpmndi:BPMNShape id="{sid}_di" bpmnElement="{sid}"{marker}>'
                 f'<dc:Bounds x="{bx}" y="{by}" width="{bw}" height="{bh}" /></bpmndi:BPMNShape>')
    for f in p.flows:
        pts = "".join(f'<di:waypoint x="{px}" y="{py}" />' for px, py in paths[f["id"]])
        x.append(f'      <bpmndi:BPMNEdge id="{f["id"]}_di" bpmnElement="{f["id"]}">{pts}</bpmndi:BPMNEdge>')
    note_y = POOL_Y + height + 30
    placed: list[int] = []
    for text, sid, nid in notes:
        bx, by, bw, bh = box(p, p.steps[sid])
        nx = bx
        ny = note_y + sum(1 for other in placed if abs(other - nx) < 150) * 52
        placed.append(nx)
        x.append(f'      <bpmndi:BPMNShape id="note_{nid}_di" bpmnElement="note_{nid}">'
                 f'<dc:Bounds x="{nx}" y="{ny}" width="140" height="44" /></bpmndi:BPMNShape>')
        x.append(f'      <bpmndi:BPMNEdge id="assoc_{nid}_di" bpmnElement="assoc_{nid}">'
                 f'<di:waypoint x="{bx + bw // 2}" y="{by + bh}" /><di:waypoint x="{nx + 20}" y="{ny}" /></bpmndi:BPMNEdge>')
    x += ['    </bpmndi:BPMNPlane>', '  </bpmndi:BPMNDiagram>', '</bpmn:definitions>', '']
    return "\n".join(x)


PALETTE = {"lane": "#f7f8fa", "lane_alt": "#eef1f5", "line": "#3c4652", "task": "#ffffff", "ai": "#ece6fb",
           "ai_line": "#6a4bc4", "system": "#e7ebf0", "client": "#e6f3ef", "gate": "#1f7a4d", "pain": "#c0392b",
           "mot": "#d68910", "fix": "#1f7a4d", "text": "#1d2430", "muted": "#5b6573"}


def svg(p: Process, subtitle: str = "", pains: list[dict] | None = None, legend: bool = True) -> str:
    """The map as SVG: lanes, shapes, flows, numbered pain-point (P) and moment-of-truth (M) badges, and a legend.

    `pains` (the As-Is pain points) lets a To-Be map list, in its legend, which pain each redesigned step fixes.
    """
    paths = layout(p)
    width, height = size(p)
    notes = p.pain_points + p.moments
    fixed = [{"id": f"✓{x['id']}", "text": f"Fixed: {x['text']}"} for x in (pains or [])
             if any(x["id"] in st.get("fixes", []) for st in p.steps.values())]
    left = p.pain_points or fixed
    legend_rows = max(len(left), len(p.moments), 1) + 2
    total_w, total_h = POOL_X * 2 + width, (POOL_Y + height + 70 + legend_rows * 22 + 60) if legend else POOL_Y * 2 + height
    c = PALETTE
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}" '
         'font-family="Inter, Helvetica, Arial, sans-serif">',
         f'<!-- Generated by scripts/maps.py. Simulated example, not real bank data. -->',
         f'<rect width="100%" height="100%" fill="#ffffff"/>',
         '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
         f'<path d="M0,0 L10,5 L0,10 z" fill="{c["line"]}"/></marker></defs>']
    for i, lane in enumerate(p.lanes):
        y = lane_y(p, lane["id"])
        o.append(f'<rect x="{POOL_X}" y="{y}" width="{width}" height="{LANE_H}" fill="{c["lane"] if i % 2 == 0 else c["lane_alt"]}" stroke="#c9cfd8"/>')
        o.append(f'<rect x="{POOL_X}" y="{y}" width="{HEADER_W}" height="{LANE_H}" fill="#dde3ea" stroke="#c9cfd8"/>')
        cx, cy = POOL_X + HEADER_W // 2, y + LANE_H // 2
        name_lines = textwrap.wrap(lane["name"], 18)
        for j, line in enumerate(name_lines):
            lx = cx + (j - (len(name_lines) - 1) / 2) * 14
            o.append(f'<text x="{lx}" y="{cy}" transform="rotate(-90 {lx} {cy})" text-anchor="middle" dominant-baseline="middle" '
                     f'font-size="12" font-weight="600" fill="{c["text"]}">{escape(line)}</text>')
    labels: list[str] = []  # drawn after the shapes, so no box hides a branch label
    for f in p.flows:
        pts = " ".join(f"{px},{py}" for px, py in paths[f["id"]])
        o.append(f'<polyline points="{pts}" fill="none" stroke="{c["line"]}" stroke-width="1.4" marker-end="url(#arrow)"/>')
        if f.get("label"):
            pts_ = paths[f["id"]]
            segs = list(zip(pts_, pts_[1:]))
            if p.steps[f["from"]]["type"] == "gateway" and len(segs) > 1 and segs[0][0][1] == segs[0][1][1]:
                segs = segs[1:]  # a branch that turns is labelled after the turn, clear of its sibling branch
            (x1, y1), (x2, y2) = next((sg for sg in segs if abs(sg[1][0] - sg[0][0]) + abs(sg[1][1] - sg[0][1]) >= 36), segs[0])
            if y1 == y2:  # horizontal: just after the turn, above the line
                lx, ly, anchor = x1 + (min(60, abs(x2 - x1) // 2) if x2 > x1 else -min(60, abs(x2 - x1) // 2)), y1 - 6, "middle"
            else:  # vertical: beside the line, near its start
                if p.steps[f["from"]]["type"] == "gateway":  # right of the line, clear of the gateway's title
                    lx, ly, anchor = x1 + 6, y1 + (22 if y2 > y1 else -48), "start"
                else:
                    lx, ly, anchor = x1 - 6, y1 + (22 if y2 > y1 else -14), "end"
            labels.append(f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" font-size="10.5" fill="{c["muted"]}" '
                          f'paint-order="stroke" stroke="#ffffff" stroke-width="3">{escape(f["label"])}</text>')
    for sid, s in p.steps.items():
        bx, by, bw, bh = box(p, s)
        cx, cy = bx + bw // 2, by + bh // 2
        t = s["type"]
        if t in {"start", "timer", "end"}:
            stroke = 3 if t == "end" else 1.6
            o.append(f'<circle cx="{cx}" cy="{cy}" r="{EV // 2}" fill="#ffffff" stroke="{c["line"]}" stroke-width="{stroke}"/>')
            if t == "timer":
                o.append(f'<circle cx="{cx}" cy="{cy}" r="{EV // 2 - 5}" fill="none" stroke="{c["line"]}"/>'
                         f'<path d="M{cx},{cy - 9} L{cx},{cy} L{cx + 6},{cy + 3}" stroke="{c["line"]}" fill="none"/>')
            for j, line in enumerate(textwrap.wrap(s["label"], 18)):
                o.append(f'<text x="{cx}" y="{by + bh + 14 + j * 13}" text-anchor="middle" font-size="10.5" fill="{c["text"]}">{escape(line)}</text>')
            continue
        if t == "gateway":
            o.append(f'<polygon points="{cx},{by} {bx + bw},{cy} {cx},{by + bh} {bx},{cy}" fill="#fff8e6" stroke="{c["line"]}" stroke-width="1.4"/>')
            o.append(f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" font-size="16" font-weight="700" fill="{c["line"]}">×</text>')
            o.append(f'<text x="{cx}" y="{by - 6}" text-anchor="middle" font-size="10.5" fill="{c["text"]}" font-weight="600" paint-order="stroke" stroke="#ffffff" stroke-width="3">{escape(s["label"])}</text>')
            continue
        fill = {"ai": c["ai"], "system": c["system"], "client": c["client"]}.get(t, c["task"])
        stroke, sw = (c["gate"], 3) if s.get("gate") else (c["ai_line"], 1.8) if t == "ai" else (c["line"], 1.2)
        dash = ' stroke-dasharray="5 3"' if t == "ai" else ""
        o.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')
        tag = "AI" if t == "ai" else "APPROVE" if s.get("gate") else "SYSTEM" if t == "system" else ""
        if tag:
            tcol = c["ai_line"] if t == "ai" else c["gate"] if s.get("gate") else c["muted"]
            o.append(f'<text x="{bx + 7}" y="{by + 13}" font-size="9" font-weight="700" letter-spacing="0.6" fill="{tcol}">{tag}</text>')
        lines = textwrap.wrap(s["label"], 20)
        top = cy - (len(lines) - 1) * 6.5 + (4 if tag else 3)
        for j, line in enumerate(lines):
            o.append(f'<text x="{cx}" y="{top + j * 13}" text-anchor="middle" font-size="11" fill="{c["text"]}">{escape(line)}</text>')
    o += labels
    badges: dict[str, list[tuple[str, str]]] = {}
    for n in p.pain_points:
        badges.setdefault(n["step"], []).append((n["id"], c["pain"]))
    for n in p.moments:
        badges.setdefault(n["step"], []).append((n["id"], c["mot"]))
    for s in p.steps.values():
        for fix in s.get("fixes", []):
            badges.setdefault(s["id"], []).append((f"✓{fix}", c["fix"]))
    for sid, items in badges.items():
        bx, by, bw, bh = box(p, p.steps[sid])
        for k, (label, col) in enumerate(items):
            w = 14 + 6.5 * len(label)
            x0 = bx + bw - w + 6 - k * (w + 3)
            o.append(f'<rect x="{x0}" y="{by - 9}" width="{w}" height="17" rx="8.5" fill="{col}"/>'
                     f'<text x="{x0 + w / 2}" y="{by + 3.5}" text-anchor="middle" font-size="10" font-weight="700" fill="#ffffff">{escape(label)}</text>')
    if not legend:
        o.append('</svg>')
        return "\n".join(o)
    y = POOL_Y + height + 34
    o.append(f'<text x="{POOL_X}" y="{y}" font-size="14" font-weight="700" fill="{c["text"]}">{escape(p.title)}</text>')
    if subtitle:
        o.append(f'<text x="{POOL_X}" y="{y + 18}" font-size="11" fill="{c["muted"]}">{escape(subtitle)}</text>')
    y += 38
    key = [("task", "Person does it"), ("gate", "Human approval gate"), ("ai", "AI step (drafts only)"),
           ("system", "System or rules"), ("client", "Client does it")]
    present = {"gate" if st.get("gate") else st["type"] for st in p.steps.values()}
    key = [(kind, text) for kind, text in key if kind in present]
    kx = POOL_X
    for kind, text in key:
        fill = {"ai": c["ai"], "system": c["system"], "client": c["client"]}.get(kind, c["task"])
        stroke, sw = (c["gate"], 3) if kind == "gate" else (c["ai_line"], 1.8) if kind == "ai" else (c["line"], 1.2)
        dash = ' stroke-dasharray="5 3"' if kind == "ai" else ""
        o.append(f'<rect x="{kx}" y="{y - 13}" width="34" height="18" rx="5" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>'
                 f'<text x="{kx + 42}" y="{y}" font-size="11.5" fill="{c["text"]}">{escape(text)}</text>')
        kx += 50 + 7 * len(text)
    y += 34
    half = (width) // 2
    for group, col0 in ((left, 0), (p.moments, half)):
        for k, n in enumerate(group):
            col = c["fix"] if n["id"].startswith("✓") else c["pain"] if n["id"].startswith("P") else c["mot"]
            yy = y + k * 20
            o.append(f'<rect x="{POOL_X + col0}" y="{yy - 12}" width="30" height="16" rx="8" fill="{col}"/>'
                     f'<text x="{POOL_X + col0 + 15}" y="{yy}" text-anchor="middle" font-size="10" font-weight="700" fill="#fff">{escape(n["id"])}</text>'
                     f'<text x="{POOL_X + col0 + 38}" y="{yy}" font-size="11.5" fill="{c["text"]}">{escape(n["text"])}</text>')
    o.append('</svg>')
    return "\n".join(o)


def svg_slice(p: Process, col_from: int, col_to: int, note_left: str = "", note_right: str = "") -> str:
    """Columns col_from..col_to of the map, with the lane names kept on the left, for a slide that shows half a map
    at a readable size. Flows crossing the cut are clipped; a note at each cut says where the map continues."""
    full = svg(p, legend=False)
    inner = full[full.index(">") + 1: full.rindex("</svg>")]
    _, height = size(p)
    header = POOL_X + HEADER_W
    shift = col_from * COL_W
    width = header + (col_to - col_from + 1) * COL_W + POOL_X
    total_h = POOL_Y * 2 + height
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total_h + 26}" viewBox="0 0 {width} {total_h + 26}" '
         'font-family="Inter, Helvetica, Arial, sans-serif">',
         f'<rect width="100%" height="100%" fill="#ffffff"/>',
         f'<defs><clipPath id="lanes"><rect x="0" y="0" width="{header}" height="{total_h}"/></clipPath>'
         f'<clipPath id="body"><rect x="{header}" y="0" width="{width - header}" height="{total_h}"/></clipPath></defs>',
         f'<g clip-path="url(#body)"><g transform="translate({-shift},0)">{inner}</g></g>',
         f'<g clip-path="url(#lanes)">{inner}</g>']
    if note_left:
        o.append(f'<text x="{header + 6}" y="{total_h + 18}" font-size="13" fill="#5b6573">{escape(note_left)}</text>')
    if note_right:
        o.append(f'<text x="{width - POOL_X}" y="{total_h + 18}" font-size="13" text-anchor="end" fill="#5b6573">{escape(note_right)}</text>')
    o.append("</svg>")
    return "\n".join(o)
