# KPI model

- **kpis:** (decided) The model measures cycle time (days from first request to account live), touch time (staff hours per case), first-pass rate (share of cases with no rework loop) and rework (loops per case), plus client touches (separate requests sent to the client), because those are the gains the redesign claims.
- **review-kpis:** (default, owner to confirm) For periodic review it also measures the share of reviews finished by their due date, because overdue reviews are the operational-risk side of the process.
- **simulated-cases:** (decided) KPIs are computed from a simulated set of cases walked through each map's steps, with a fixed seed, so the numbers can be remade exactly.
- **assumptions-visible:** (decided) Every simulation input sits in one assumptions table with its value, its unit and its basis (a source or `(guess)`), so a reader can argue with any of them.
- **baseline-vs-to-be:** (decided) Each KPI is shown for As-Is and To-Be side by side, with the change (in percentage points for shares), and a sensitivity run with today's queue times shows how much of the gain depends on shorter queues.
- **assumptions-justified:** (decided) A document gives the reason for every simulation input's value, with a source where one exists and otherwise says it is a judgment, and compares the model's outputs with published figures, so a reader can see which numbers are anchored and which are guesses.
- **sheets-ready:** (decided) The model ships as one workbook that imports into Google Sheets as is: a read-me tab, assumptions, cases, KPIs and a tab shaped for Looker Studio.
- **numbers-from-model:** (decided) Every KPI number quoted anywhere else comes from the model's output, so the deck and the docs can't drift from it.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `kpis` | `scripts/simulate.py` | `test_kpis_present_for_each_map_and_case_type` |
| `review-kpis` | `scripts/simulate.py` | `test_review_kpis_on_time_is_cycle_within_the_lead_time` |
| `simulated-cases` | `scripts/simulate.py`, `model/assumptions.yaml` | `test_simulated_cases_same_seed_same_numbers`, `test_simulated_cases_follow_the_map_flows`, `test_simulated_cases_branch_by_case_type_and_keep_case_decisions` |
| `assumptions-visible` | `model/assumptions.yaml`, `scripts/workbook.py` | `test_assumptions_visible_every_key_used_and_every_key_defined`, `test_assumptions_visible_each_has_value_unit_and_basis` |
| `baseline-vs-to-be` | `scripts/simulate.py`, `scripts/workbook.py`, `scripts/charts.py` | `test_baseline_vs_to_be_change_in_percent_or_points`, `test_baseline_vs_to_be_sensitivity_with_todays_queues` |
| `assumptions-justified` | `model/assumption-reasons.yaml`, `docs/assumptions.md`, `scripts/build.py` | `test_assumptions_justified_every_input_has_a_reason`, `test_assumptions_justified_doc_shows_every_input_with_its_value` |
| `sheets-ready` | `scripts/workbook.py`, `scripts/build.py` | `test_sheets_ready_workbook_has_the_tabs_and_says_simulated`, `test_workbook_is_byte_identical_when_remade` |
| `numbers-from-model` | `scripts/simulate.py`, `scripts/build.py`, `scripts/charts.py` | `test_simulated_cases_same_seed_same_numbers`, `test_numbers_traced_wrong_marker_fails` |
