# Process maps

- **as-is-map:** (decided) An As-Is BPMN 2.0 map shows today's onboarding and periodic review end to end, in swimlanes per role, so the reader sees where time and rework go.
- **pain-points:** (decided) The As-Is map marks each pain point on the step where it happens, each with its cause in a few words.
- **to-be-map:** (decided) A To-Be BPMN 2.0 map shows the redesign, with each AI step drawn as its own task so the reader sees exactly what the AI does.
- **human-gates:** (decided) In the To-Be map, every AI output that changes a client's status, risk rating or file passes a named human approval task first, because the AI reads and a person decides.
- **moments-of-truth:** (decided) Both maps mark the same two or three client moments of truth, the points where the client forms an opinion of the bank, so the redesign can be judged from the client's side.
- **decline-path:** (decided) Both maps show where a client is declined or the relationship exited, because a KYC process that can only say yes isn't a control.
- **review-skips-asks:** (decided) In the To-Be map a periodic review with nothing missing skips the client request entirely, because asking a client for what the bank already holds is the pain being removed.
- **opens-in-bpmn-io:** (decided) Both maps are valid BPMN 2.0 XML with diagram layout, so they open and render in bpmn.io and Camunda Modeler without changes.
- **one-source:** (default, owner to confirm) Each map is generated from one readable process file, so the XML, the picture and the KPI model can't disagree, and the committed files always match it about the steps.
- **pictures:** (decided) Each map also comes as an image good enough for a slide.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `as-is-map` | `model/as-is.yaml`, `scripts/maps.py` | `test_as_is_map_is_well_formed_with_a_lane_per_role`, `test_as_is_map_covers_onboarding_and_periodic_review` |
| `pain-points` | `model/as-is.yaml`, `scripts/maps.py` | `test_pain_points_each_sit_on_a_step_with_a_cause` |
| `to-be-map` | `model/to-be.yaml`, `scripts/maps.py` | `test_to_be_map_is_well_formed_and_ai_steps_are_their_own_tasks` |
| `human-gates` | `model/to-be.yaml`, `scripts/maps.py` | `test_human_gates_no_ai_output_reaches_an_effect_ungated`, `test_human_gates_an_ungated_effect_is_caught` |
| `moments-of-truth` | `model/as-is.yaml`, `model/to-be.yaml`, `scripts/maps.py` | `test_moments_of_truth_are_the_same_two_or_three_in_both_maps` |
| `decline-path` | `model/as-is.yaml`, `model/to-be.yaml` | `test_decline_path_reachable_from_compliance_in_both_maps` |
| `review-skips-asks` | `model/to-be.yaml` | `test_review_skips_asks_a_review_can_reach_screening_without_the_client` |
| `opens-in-bpmn-io` | `scripts/maps.py` | `test_opens_in_bpmn_io_every_element_has_layout` |
| `one-source` | `model/as-is.yaml`, `model/to-be.yaml`, `scripts/maps.py`, `scripts/build.py` | `test_one_source_generated_files_match_the_model` |
| `pictures` | `scripts/maps.py`, `scripts/build.py` | `test_pictures_exist_at_slide_resolution` |
