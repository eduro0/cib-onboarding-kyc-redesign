"""Tests for the KPI model: the simulation, its assumptions, the workbook and the charts.

Implements: kpi-model/kpis, kpi-model/review-kpis, kpi-model/simulated-cases, kpi-model/assumptions-visible, kpi-model/baseline-vs-to-be, kpi-model/sheets-ready, kpi-model/numbers-from-model
"""

import json
import struct
import sys
from pathlib import Path

import yaml
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import maps  # noqa: E402
import simulate  # noqa: E402

NUMBERS = json.loads((ROOT / "build" / "numbers.json").read_text())
KPIS = ("cycle_days", "touch_hours", "first_pass", "rework", "client_touches")


def test_kpis_present_for_each_map_and_case_type():
    for case in ("onb", "rev"):
        for kpi in KPIS:
            for side in ("as_is", "to_be"):
                assert f"{case}_{kpi}_{side}" in NUMBERS


def test_review_kpis_on_time_is_cycle_within_the_lead_time():
    result = simulate.run()
    lead = simulate.load_assumptions()["review_lead_days"]
    for name, side in (("as-is", "as_is"), ("to-be", "to_be")):
        done = [c for c in result.cases if c["process"] == name and c["case_type"] == "review" and not c["declined"]]
        assert NUMBERS[f"rev_on_time_{side}"] == round(sum(c["cycle_days"] <= lead for c in done) / len(done), 2)


def test_baseline_vs_to_be_change_in_percent_or_points():
    for case in ("onb", "rev"):
        for kpi in KPIS:
            a, b = NUMBERS[f"{case}_{kpi}_as_is"], NUMBERS[f"{case}_{kpi}_to_be"]
            if kpi in simulate.SHARES:  # a share changes in percentage points, never a relative percentage
                assert f"{case}_{kpi}_change_pct" not in NUMBERS
                assert NUMBERS[f"{case}_{kpi}_change_pts"] == round((b - a) * 100)
            else:
                assert NUMBERS[f"{case}_{kpi}_change_pct"] == round((b - a) / a * 100, 0)
    assert NUMBERS["rev_on_time_change_pts"] == round((NUMBERS["rev_on_time_to_be"] - NUMBERS["rev_on_time_as_is"]) * 100)


def test_baseline_vs_to_be_sensitivity_with_todays_queues():
    for case in ("onb", "rev"):
        assert NUMBERS[f"{case}_cycle_days_to_be"] < NUMBERS[f"{case}_cycle_days_to_be_slow_queues"] < NUMBERS[f"{case}_cycle_days_as_is"]


def test_simulated_cases_same_seed_same_numbers():
    first, second = simulate.run(), simulate.run()
    assert first.numbers == second.numbers
    simulated = {k: v for k, v in NUMBERS.items() if not k.startswith("live.")}  # live.* come from score_live.py
    assert first.numbers == simulated, "build/numbers.json is stale: run make build"


def test_simulated_cases_follow_the_map_flows():
    result = simulate.run()
    flows = {name: {(f["from"], f["to"]) for f in maps.load(ROOT / "model" / f"{name}.yaml").flows}
             for name in ("as-is", "to-be")}
    for case in result.cases:
        for pair in zip(case["path"], case["path"][1:]):
            assert pair in flows[case["process"]], (case["id"], pair)


def test_simulated_cases_branch_by_case_type_and_keep_case_decisions():
    cases = [c for c in simulate.run().cases if c["process"] == "to-be" and c["case_type"] == "review"]
    skipped = [c for c in cases if "upload" not in c["path"]]
    assert abs(len(skipped) / len(cases) - 0.4) < 0.06  # tobe.ask_client.p is 0.6 for reviews
    for c in cases:
        if "upload" in c["path"]:
            assert c["path"].count("gw_ask") == c["path"].count("upload"), c["id"]  # once asked, stays asked
        assert c["path"].count("gw_risk") <= 1, c["id"]  # risk is decided once per case
    onboarding = [c for c in simulate.run().cases if c["process"] == "to-be" and c["case_type"] == "onboarding"]
    assert all("upload" in c["path"] and "approve" in c["path"] for c in onboarding if not c["declined"])


def test_assumptions_visible_every_key_used_and_every_key_defined():
    assumptions = simulate.load_assumptions()
    used = set()
    for name in ("as-is", "to-be"):
        proc = maps.load(ROOT / "model" / f"{name}.yaml")
        used |= {s[k] for s in proc.steps.values() for k in ("touch", "wait") if k in s}
        used |= {f["p"] for f in proc.flows if "p" in f}
    assert used <= set(assumptions), f"undefined: {used - set(assumptions)}"
    unused = {k for k in assumptions if "." in k} - used
    assert not unused, f"defined but never used: {unused}"


def test_assumptions_visible_each_has_value_unit_and_basis():
    raw = yaml.safe_load((ROOT / "model" / "assumptions.yaml").read_text())
    for group in raw.values():
        for key, a in group.items():
            assert {"value", "unit", "basis"} <= set(a), key
            assert a["basis"] == "(guess)" or a["basis"].startswith("[src:"), key


def test_sheets_ready_workbook_has_the_tabs_and_says_simulated():
    wb = load_workbook(ROOT / "deliverables" / "kpi-model.xlsx")
    assert wb.sheetnames == ["Read me", "Assumptions", "Cases", "KPIs", "Looker data"]
    for ws in wb.worksheets:
        top = " ".join(str(c.value) for row in ws.iter_rows(max_row=2) for c in row if c.value)
        assert "simulated" in top.lower(), ws.title
    columns = {"Cycle time": "D", "Touch time": "E", "Rework": "F", "Client touches": "G", "First-pass rate": "H",
               "Reviews on time": "J"}
    rows = [r for r in wb["KPIs"].iter_rows(min_row=3, values_only=True) if r[0] in columns]
    assert len(rows) == 11
    for label, case_type, as_is, to_be, *_ in rows:
        col = columns[label]
        for formula, process in ((as_is, "as-is"), (to_be, "to-be")):
            assert formula.startswith(f"=AVERAGEIFS(Cases!{col}3:"), (label, formula)
            assert f'"{process}"' in formula and f'"{case_type}"' in formula and formula.endswith(",0)")


def test_workbook_is_byte_identical_when_remade(tmp_path):
    import workbook
    result = simulate.run()
    workbook.write(result.cases, result.numbers, tmp_path / "again.xlsx")
    assert (tmp_path / "again.xlsx").read_bytes() == (ROOT / "deliverables" / "kpi-model.xlsx").read_bytes()


def test_charts_exist_at_slide_size():
    for name in ("kpi-onboarding", "kpi-review"):
        png = (ROOT / "deliverables" / "charts" / f"{name}.png").read_bytes()
        width, height = struct.unpack(">II", png[16:24])
        assert width >= 1600 and height >= 700
