# Assistant

- **one-step:** (decided) The assistant serves the redesigned document-review step: it reads a corporate client's KYC pack and drafts the analyst's review, because that step carries most of the touch time and rework.
- **llm-reads-rules-decide:** (decided) The model only extracts and drafts; deterministic rules decide what is missing, what changed and which review triggers fire, so every flag can be explained.
- **human-approves:** (decided) The assistant's output is a draft an analyst approves, edits or rejects, and only the text the analyst approved, as they left it, can be released, in a separate step after they have read it.
- **one-client-request:** (decided) All missing items go into one consolidated client request, because repeated requests are the main client pain.
- **synthetic-packs:** (decided) It is demonstrated on made-up companies and documents only.
- **runs-offline:** (decided) It runs and is tested without a key or network, replaying recorded model replies, so anyone can see it work.
- **live-scored:** (decided) Every sample pack has been run on real models through OpenRouter, at least the free default and one paid model; the replies are committed with model, date, tokens and cost, and a committed script scores them against the hand-written replies, so the claim that a real model's output works with the rules rests on evidence.
- **cost-first:** (decided) A live run on OpenRouter prints its estimated cost and waits for a yes, and defaults to a free model.
- **gem-pack:** (decided) The same behaviour ships as instructions and knowledge files to paste into a Gemini Gem or a custom GPT, so the same assistant can be tried in free consumer tools.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `one-step` | `assistant/rules.py`, `assistant/report.py` | `test_one_step_draft_has_every_section`, `test_onboarding_flags_missing_documents_and_director_mismatch`, `test_review_with_changes_triggers_a_refresh`, `test_review_with_no_change_asks_nothing`, `test_review_no_change_needs_positive_evidence`, `test_review_reports_a_shareholder_who_left`, `test_no_owner_over_threshold_asks_who_controls`, `test_intermediate_companies_need_their_own_evidence` |
| `llm-reads-rules-decide` | `assistant/rules.py`, `assistant/llm.py`, `assistant/requirements.yaml`, `prompts/extract.md` | `test_llm_reads_rules_decide_beneficial_owners_from_the_chain`, `test_llm_reads_rules_decide_flags_follow_the_facts_not_the_model`, `test_llm_reads_rules_decide_a_quote_not_in_the_document_is_dropped_and_flagged`, `test_llm_reads_rules_decide_a_quote_must_contain_the_claimed_value`, `test_llm_reads_rules_decide_document_types_come_from_the_documents` |
| `human-approves` | `assistant/report.py`, `assistant/cli.py` | `test_human_approves_review_only_writes_a_draft`, `test_human_approves_release_needs_a_ticked_decision_and_a_name`, `test_human_approves_an_edited_draft_releases_exactly_the_edited_text`, `test_human_approves_a_rejected_draft_is_never_released` |
| `one-client-request` | `assistant/rules.py`, `assistant/report.py` | `test_one_client_request_lists_every_missing_item_once` |
| `synthetic-packs` | `assistant/samples/README.md` | `test_synthetic_packs_are_declared_fictional` |
| `runs-offline` | `assistant/llm.py`, `assistant/cli.py`, `assistant/__main__.py` | `test_runs_offline_without_key_or_network` |
| `live-scored` | `scripts/live_run.py`, `scripts/score_live.py`, `assistant/llm.py`, `assistant/live/results.md`, `assistant/README.md` | `test_live_scored_every_pack_has_a_free_and_a_paid_recording`, `test_live_scored_a_perfect_reply_scores_perfect_and_a_missing_fact_is_caught`, `test_live_scored_results_file_is_fresh`, `test_live_scored_readme_traces_its_numbers` |
| `cost-first` | `assistant/llm.py`, `assistant/cli.py` | `test_cost_first_live_run_needs_yes` |
| `gem-pack` | `deliverables/gem/instructions.md`, `deliverables/gem/README.md` | `test_gem_pack_is_small_and_says_what_to_paste_where` |
