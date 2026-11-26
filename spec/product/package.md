# Package

- **deck:** (decided) A slide deck that imports into Google Slides tells the story in about twelve slides: the problem, As-Is, To-Be, gates and moments of truth, KPIs, the assistant, the roadmap, change risks and the sources.
- **roadmap:** (decided) A phased implementation roadmap says what ships in each phase, who has to agree, and the KPI that decides whether the next phase starts.
- **change-risks:** (decided) A change-risk register lists each risk to staff, clients, controls and regulators, with its likelihood, impact, mitigation, owner and the signal that would show it happening.
- **dashboard-guide:** (decided) A step-by-step guide builds the Looker Studio dashboard on the Sheets workbook, chart by chart.
- **notebook-pack:** (decided) A NotebookLM pack lists the public sources to load and the questions that show it answering from them.
- **site-pack:** (decided) A Google Sites pack gives the page structure and the copy for each page, linking every deliverable except the assistant, so the site can be built in under an hour. The assistant has no site page (owner decision): the deck and the access guide cover it.
- **owner-checklist:** (decided) One checklist says, in order, everything only the owner can do (uploads, accounts, publishing), so the steps that need a person's own accounts are clear.
- **access-guide:** (decided) An access guide, sent with the site link, lists every published file, what it holds, where its data comes from and whether it opens without a Google sign-in.
- **readable-tables:** (decided) Every table in a Word export for Google Docs has borders, a shaded header row, column widths sized to its content and a page wide enough for its columns, so it reads in Google Docs.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `deck` | `scripts/deck.py`, `scripts/build.py` | `test_deck_tells_the_story_in_about_twelve_slides`, `test_deck_every_number_comes_from_the_model_or_a_source`, `test_deck_shows_the_maps_and_charts` |
| `roadmap` | `docs/roadmap.md`, `scripts/build.py` | `test_roadmap_each_phase_says_what_ships_who_agrees_and_its_gate`, `test_docs_export_to_word_with_numbered_sources_and_real_lists` |
| `change-risks` | `docs/change-risks.md`, `scripts/build.py` | `test_change_risks_register_covers_every_area_with_every_field`, `test_docs_export_to_word_with_numbered_sources_and_real_lists` |
| `dashboard-guide` | `docs/dashboard-guide.md` | `test_dashboard_guide_names_fields_that_exist_in_the_looker_tab`, `test_dashboard_guide_never_sums_across_processes_or_case_types` |
| `notebook-pack` | `docs/notebook-pack.md` | `test_notebook_pack_loads_only_recorded_sources_and_asks_five_questions` |
| `site-pack` | `docs/site-pack.md` | `test_site_pack_has_every_page_and_links_every_deliverable` |
| `access-guide` | `docs/access-guide.md`, `scripts/build.py` | `test_access_guide_lists_every_published_file_with_its_data_and_access`, `test_access_guide_exports_to_word` |
| `readable-tables` | `scripts/build.py` | `test_exported_tables_have_borders_header_and_fitted_columns` |
| `owner-checklist` | `docs/owner-checklist.md` | `test_owner_checklist_covers_every_owner_step_in_order_with_times` |
