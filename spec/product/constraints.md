# Constraints

- **public-only:** (decided) Everything is built from public material only, because the project is a public portfolio piece and must not rest on anything confidential.
- **no-firm-names:** (decided) No deliverable names a real client firm or states any internal fact about a real bank, so nothing can be read as a leak.
- **simulated-labelled:** (decided) Every number that isn't quoted from a public source is simulated, and each deliverable that shows one says so on the same page.
- **sourced-claims:** (decided) Every claim about rules, regulators or the industry cites an entry in `sources/`, so a reviewer at the bank can check it; the fictional sample packs, which make no claims, are the only exemption.
- **no-private-people:** (decided) Deliverables name no private individuals and no recruiting details, because the site and deck are public.
- **free-tools:** (decided) Everything runs on free tools and free accounts; the only paid path is OpenRouter, and it needs the owner's yes first.
- **unnamed-bank:** (decided) The redesign is for "a CIB branch in Hong Kong" rather than BBVA itself, so it shows the method without claiming knowledge of BBVA's processes.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `public-only` | reviewer | — |
| `no-firm-names` | `checks/project/public_clean.py` | `test_no_firm_names_term_in_a_deck_fails` |
| `simulated-labelled` | `checks/project/public_clean.py` | `test_simulated_labelled_number_without_label_fails`, `test_simulated_labelled_each_slide_is_checked` |
| `sourced-claims` | `checks/project/public_clean.py` | `test_sourced_claims_regulator_paragraph_without_citation_fails`, `test_sourced_claims_spelled_out_regulators_need_a_citation`, `test_sourced_claims_source_of_wealth_is_not_a_citation`, `test_sourced_claims_only_listed_fictional_samples_are_exempt` |
| `no-private-people` | `checks/project/public_clean.py` | `test_no_private_people_local_term_in_docs_fails` |
| `free-tools` | not yet | — |
| `unnamed-bank` | reviewer | — |
