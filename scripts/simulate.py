"""Simulate cases through the As-Is and To-Be maps and compute the KPIs.

Implements: kpi-model/kpis, kpi-model/review-kpis, kpi-model/simulated-cases, kpi-model/baseline-vs-to-be, kpi-model/numbers-from-model

Each case starts at its map's start event for its type (onboarding or review) and walks the flows. A task adds its
touch hours and its waiting days, each drawn around the assumption's value. At a gateway, a branch with `when` is
taken by case type, and a branch with `p` is taken with that probability; the remaining branch takes the rest.
A flow that goes back to an earlier column is rework. A gateway marked sticky (does the case need the
client? is it high risk? was it approved?) is decided once per case and keeps its answer on a rework loop. Every random draw comes from a generator seeded by the run
seed plus the case's identity, so the same assumptions always give the same cases and the same numbers.

KPIs, per map and case type, over cases that were not declined:
- cycle_days: mean elapsed days from start to end; cycle_days_p90: the 90th percentile
- touch_hours: mean staff hours per case
- first_pass: share of cases with no rework loop
- rework: mean rework loops per case
- client_touches: mean separate asks to the client (visits to a client-lane task)
- on_time (reviews only): share finished within the review lead time
plus the declined share, staff hours per year at the assumed volumes, and a sensitivity run of the To-Be map in
which every human step keeps today's queue time (`*_cycle_days_to_be_slow_queues`). Changes in a share (first
pass, on time) are in percentage points.
"""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass
from pathlib import Path

import yaml

import maps

ROOT = Path(__file__).resolve().parent.parent
MAPS = {"as-is": ROOT / "model" / "as-is.yaml", "to-be": ROOT / "model" / "to-be.yaml"}
SIDE = {"as-is": "as_is", "to-be": "to_be"}
CASE = {"onboarding": "onb", "review": "rev"}
KPI_ROUND = {"cycle_days": 1, "cycle_days_p90": 1, "touch_hours": 1, "first_pass": 2, "rework": 2,
             "client_touches": 2}
SHARES = {"first_pass"}  # shares change in percentage points, never as a relative percentage
# Sensitivity: To-Be human steps keep today's queue times (To-Be wait key -> the As-Is step it replaces).
TODAYS_QUEUES = {"tobe.approve_request.wait": "asis.request_docs.wait", "tobe.upload.wait": "asis.send_docs.wait",
                 "tobe.review_draft.wait": "asis.check_pack.wait", "tobe.decide_hits.wait": "asis.clear_hits.wait",
                 "tobe.confirm_rating.wait": "asis.rate.wait", "tobe.edd_approve.wait": "asis.edd.wait",
                 "tobe.qc_signoff.wait": "asis.qc.wait", "tobe.fix_file.wait": "asis.fix_file.wait",
                 "tobe.approve.wait": "asis.approve.wait", "tobe.open_accounts.wait": "asis.open_accounts.wait",
                 "tobe.update_file.wait": "asis.update_file.wait"}


@dataclass
class Result:
    cases: list[dict]
    numbers: dict


def load_assumptions(path: Path = ROOT / "model" / "assumptions.yaml") -> dict:
    """Flatten the assumptions file to {key: value}."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return {key: a["value"] for group in raw.values() for key, a in group.items()}


def tri(rng: random.Random, value: float, spread: list[float]) -> float:
    return 0.0 if value == 0 else rng.triangular(value * spread[0], value * spread[1], value)


def walk(proc: maps.Process, case_type: str, a: dict, rng: random.Random) -> dict:
    start = next(s for s in proc.steps.values() if s["type"] in {"start", "timer"} and s.get("case") == case_type)
    out = {f["from"]: [] for f in proc.flows}
    for f in proc.flows:
        out[f["from"]].append(f)
    cur, path, days, hours, rework, touches = start["id"], [], 0.0, 0.0, 0, 0
    decided: dict[str, dict] = {}  # sticky gateways: the branch this case took the first time
    for _ in range(200):
        step = proc.steps[cur]
        path.append(cur)
        if "wait" in step:
            days += tri(rng, a[step["wait"]], a["wait_spread"])
        if "touch" in step:
            hours += tri(rng, a[step["touch"]], a["touch_spread"])
        if step["lane"] == "client" and step["type"] == "client":
            touches += 1
        if step["type"] == "end":
            break
        flows = out[cur]
        if len(flows) == 1:
            nxt = flows[0]
        elif step.get("sticky") and cur in decided:
            nxt = decided[cur]
        else:
            nxt = next((f for f in flows if f.get("when") == case_type), None)
            if nxt is None:
                u, acc = rng.random(), 0.0
                for f in (f for f in flows if "p" in f):
                    p = a[f["p"]]
                    acc += p[case_type] if isinstance(p, dict) else p
                    if u < acc:
                        nxt = f
                        break
                if nxt is None:
                    nxt = next(f for f in flows if "p" not in f and "when" not in f)
            decided[cur] = nxt
        if proc.steps[nxt["to"]]["col"] < step["col"]:
            rework += 1
        cur = nxt["to"]
    else:
        raise RuntimeError(f"{proc.id}: case never reached an end event")
    declined = "declin" in proc.steps[cur]["label"].lower()
    return {"path": path, "cycle_days": days, "touch_hours": hours, "rework": rework, "client_touches": touches,
            "first_pass": rework == 0, "declined": declined}


def simulate_cases(a: dict, names=("as-is", "to-be")) -> list[dict]:
    cases = []
    for name in names:
        path = MAPS[name]
        proc = maps.load(path)
        for case_type, count_key in (("onboarding", "onboarding_cases"), ("review", "review_cases")):
            for i in range(a[count_key]):
                rng = random.Random(f"{a['seed']}-{name}-{case_type}-{i}")
                c = walk(proc, case_type, a, rng)
                c.update(id=f"{CASE[case_type].upper()}-{i + 1:04d}", process=name, case_type=case_type)
                if case_type == "review":
                    c["on_time"] = c["cycle_days"] <= a["review_lead_days"]
                cases.append(c)
    return cases


def run(assumptions: dict | None = None) -> Result:
    a = assumptions or load_assumptions()
    cases = simulate_cases(a)
    numbers = kpis(cases, a)
    slow = dict(a, **{k: a[v] for k, v in TODAYS_QUEUES.items()})
    slow_cases = simulate_cases(slow, ("to-be",))
    for case_type, short in CASE.items():
        done = [c for c in slow_cases if c["case_type"] == case_type and not c["declined"]]
        numbers[f"{short}_cycle_days_to_be_slow_queues"] = round(statistics.mean(c["cycle_days"] for c in done), 1)
    return Result(cases, dict(sorted(numbers.items())))


def kpis(cases: list[dict], a: dict) -> dict:
    n: dict = {}
    for name, side in SIDE.items():
        for case_type, short in CASE.items():
            group = [c for c in cases if c["process"] == name and c["case_type"] == case_type]
            done = [c for c in group if not c["declined"]]
            cycle = sorted(c["cycle_days"] for c in done)
            values = {"cycle_days": statistics.mean(cycle), "cycle_days_p90": cycle[int(0.9 * (len(cycle) - 1))],
                      "touch_hours": statistics.mean(c["touch_hours"] for c in done),
                      "first_pass": sum(c["first_pass"] for c in done) / len(done),
                      "rework": statistics.mean(c["rework"] for c in done),
                      "client_touches": statistics.mean(c["client_touches"] for c in done)}
            for kpi, v in values.items():
                n[f"{short}_{kpi}_{side}"] = round(v, KPI_ROUND[kpi])
            n[f"{short}_over_60_days_{side}"] = round(sum(c["cycle_days"] > 60 for c in done) / len(done), 2)
            n[f"{short}_declined_{side}"] = round(sum(c["declined"] for c in group) / len(group), 2)
            n[f"{short}_cases_{side}"] = len(group)
            n[f"{short}_staff_hours_year_{side}"] = round(sum(c["touch_hours"] for c in group))
            if case_type == "review":
                n[f"rev_on_time_{side}"] = round(sum(c["on_time"] for c in done) / len(done), 2)
    for short in CASE.values():
        for kpi in list(KPI_ROUND) + ["staff_hours_year"]:
            before, after = n[f"{short}_{kpi}_as_is"], n[f"{short}_{kpi}_to_be"]
            if kpi in SHARES:
                n[f"{short}_{kpi}_change_pts"] = round((after - before) * 100)
            else:
                n[f"{short}_{kpi}_change_pct"] = round((after - before) / before * 100, 0) if before else 0
    n["rev_on_time_change_pts"] = round((n["rev_on_time_to_be"] - n["rev_on_time_as_is"]) * 100)
    n["staff_hours_year_saved"] = (n["onb_staff_hours_year_as_is"] + n["rev_staff_hours_year_as_is"]
                                   - n["onb_staff_hours_year_to_be"] - n["rev_staff_hours_year_to_be"])
    n["fte_saved"] = round(n["staff_hours_year_saved"] / a["fte_hours"], 1)
    return n
