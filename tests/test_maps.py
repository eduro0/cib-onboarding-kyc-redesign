"""Tests for the process maps: the model files, the generated BPMN and the pictures.

Implements: process-maps/as-is-map, process-maps/pain-points, process-maps/to-be-map, process-maps/human-gates, process-maps/moments-of-truth, process-maps/opens-in-bpmn-io, process-maps/one-source, process-maps/pictures, process-maps/decline-path, process-maps/review-skips-asks
"""

import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import maps  # noqa: E402

NS = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL", "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
      "di": "http://www.omg.org/spec/DD/20100524/DI"}
AS_IS, TO_BE = maps.load(ROOT / "model" / "as-is.yaml"), maps.load(ROOT / "model" / "to-be.yaml")
OUT = ROOT / "deliverables" / "maps"


def test_as_is_map_is_well_formed_with_a_lane_per_role():
    assert maps.problems(AS_IS) == []
    names = " ".join(lane["name"].lower() for lane in AS_IS.lanes)
    for role in ("client", "relationship manager", "operations", "compliance", "systems"):
        assert role in names


def test_as_is_map_covers_onboarding_and_periodic_review():
    cases = {s.get("case") for s in AS_IS.steps.values() if s["type"] in {"start", "timer"}}
    assert cases == {"onboarding", "review"}


def test_pain_points_each_sit_on_a_step_with_a_cause():
    assert len(AS_IS.pain_points) >= 5
    for p in AS_IS.pain_points:
        assert p["step"] in AS_IS.steps and len(p["text"].split()) >= 5


def test_to_be_map_is_well_formed_and_ai_steps_are_their_own_tasks():
    assert maps.problems(TO_BE) == []
    ai = [s for s in TO_BE.steps.values() if s["type"] == "ai"]
    assert len(ai) >= 4
    root = ET.fromstring((OUT / "to-be.bpmn").read_text())
    names = [t.get("name") for t in root.iter(f"{{{NS['bpmn']}}}serviceTask")]
    assert sum(1 for n in names if n.startswith("AI: ")) == len(ai)


def test_human_gates_no_ai_output_reaches_an_effect_ungated():
    assert maps.ungated_ai_effects(TO_BE) == []
    assert sum(1 for s in TO_BE.steps.values() if s.get("gate")) >= 5


def test_human_gates_an_ungated_effect_is_caught():
    p = maps.Process("t", "t", [{"id": "a", "name": "A"}],
                     {"s": {"id": "s", "type": "start", "lane": "a", "col": 0},
                      "ai": {"id": "ai", "type": "ai", "lane": "a", "col": 1, "label": "x"},
                      "fx": {"id": "fx", "type": "system", "effect": True, "lane": "a", "col": 2, "label": "x"},
                      "e": {"id": "e", "type": "end", "lane": "a", "col": 3, "label": "x"}},
                     [{"id": "f1", "from": "s", "to": "ai"}, {"id": "f2", "from": "ai", "to": "fx"},
                      {"id": "f3", "from": "fx", "to": "e"}])
    assert maps.ungated_ai_effects(p) == ["ai: AI output reaches 'fx' without a human gate"]


def test_moments_of_truth_are_the_same_two_or_three_in_both_maps():
    as_is, to_be = {m["id"] for m in AS_IS.moments}, {m["id"] for m in TO_BE.moments}
    assert as_is == to_be and 2 <= len(as_is) <= 3


def test_opens_in_bpmn_io_every_element_has_layout():
    for name, proc in (("as-is", AS_IS), ("to-be", TO_BE)):
        root = ET.fromstring((OUT / f"{name}.bpmn").read_text())
        shapes = {s.get("bpmnElement") for s in root.iter(f"{{{NS['bpmndi']}}}BPMNShape")}
        edges = {e.get("bpmnElement"): e for e in root.iter(f"{{{NS['bpmndi']}}}BPMNEdge")}
        assert set(proc.steps) <= shapes
        for f in proc.flows:
            assert len(edges[f["id"]].findall("di:waypoint", NS)) >= 2
        lanes = root.findall(".//bpmn:lane", NS)
        assert {ref.text for lane in lanes for ref in lane.findall("bpmn:flowNodeRef", NS)} == set(proc.steps)


def test_one_source_generated_files_match_the_model():
    import build
    for name, proc in (("as-is", AS_IS), ("to-be", TO_BE)):
        assert (OUT / f"{name}.bpmn").read_text() == maps.bpmn_xml(proc), f"{name}.bpmn is stale: run make build"
        assert (OUT / f"{name}.svg").read_text() == maps.svg(proc, build.SIMULATED, AS_IS.pain_points), \
            f"{name}.svg is stale: run make build"


def paths_from(proc, start, avoid=()):
    nxt = {sid: [f["to"] for f in proc.flows if f["from"] == sid] for sid in proc.steps}
    seen, todo = set(), [start]
    while todo:
        cur = todo.pop()
        if cur in seen or cur in avoid:
            continue
        seen.add(cur)
        todo.extend(nxt[cur])
    return seen


def test_decline_path_reachable_from_compliance_in_both_maps():
    for proc in (AS_IS, TO_BE):
        compliance = [sid for sid, s in proc.steps.items() if s["lane"] == "compliance" and s["type"] == "task"]
        declines = {sid for sid, s in proc.steps.items() if s["type"] == "end" and "declin" in s["label"].lower()}
        assert compliance and declines
        assert all(declines & paths_from(proc, c) for c in compliance)


def test_review_skips_asks_a_review_can_reach_screening_without_the_client():
    client_steps = {sid for sid, s in TO_BE.steps.items() if s["lane"] == "client" and s["type"] != "start"}
    assert "screen" in paths_from(TO_BE, "start_review", avoid=client_steps)


def test_pictures_exist_at_slide_resolution():
    for name in ("as-is", "to-be"):
        png = (OUT / f"{name}.png").read_bytes()
        width, height = struct.unpack(">II", png[16:24])
        assert png[:8] == b"\x89PNG\r\n\x1a\n" and width >= 2400 and height >= 900
