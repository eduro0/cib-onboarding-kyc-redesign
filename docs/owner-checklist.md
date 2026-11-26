<!-- Implements: package/owner-checklist -->
# Owner checklist: publishing the package on Google tools

Everything here needs a person's own Google account or is a publishing step, so the build stops before it. Do the
steps in order; the times are estimates. Anyone rebuilding the package can follow the same steps on a free
account.

## Put the files in Google Drive

1. **Make a Drive folder and share it** (5 min). Create a folder for the package, then Share → General access →
   "Anyone with the link" (viewer), so everything the site links opens for visitors. Upload everything below
   into it.
2. **Workbook to Google Sheets** (5 min). Upload `deliverables/kpi-model.xlsx`, open it, File → Save as
   Google Sheets. Check that the KPIs tab shows numbers (its formulas recompute in Sheets).
3. **Deck to Google Slides** (5 min). Upload `deliverables/deck.pptx`, open it with Google Slides, then File →
   Save as Google Slides (Sites can only embed the converted copy). Check slides 4–7 (the maps, two slides each) and
   the fonts.
4. **Docs to Google Docs** (5 min). Upload `deliverables/docs/roadmap.docx`, `change-risks.docx` and
   `assumptions.docx`; open each with Google Docs, then File → Save as Google Docs.
5. **Maps** (5 min). Upload the four files in `deliverables/maps/` (PNG and BPMN). Optional: open `as-is.bpmn` at
   https://demo.bpmn.io to see it in a BPMN tool.

## Build the Google tools

6. **Data Studio dashboard** (30 min). Follow `docs/dashboard-guide.md` on the Sheets copy from step 2.
7. **Gemini Gem, now a Gemini skill** (15 min). Follow `deliverables/gem/README.md`; Gems are now made under
   Customize → Skills [src:gemini-gems-now-skills]. Test it on the sample pack and compare the answer with the
   prototype's. Take two screenshots of its answer for the site.
8. **Custom GPT, if your account allows it** (10 min). Same pack; skip if ChatGPT won't let you create one.
9. **Gemini Notebook** (20 min). Follow `docs/notebook-pack.md`.
10. **Google Site** (60 min). Follow `docs/site-pack.md`, then publish.

## Optional

11. **Live assistant run** (10 min). Put `OPENROUTER_API_KEY` in `.env`, then run the live command in
    `assistant/README.md`. It prints the cost first (the default model is free) and needs `--yes`. Add `--record`
    to keep the real reply as the pack's replay.

## Before sharing

12. **Check it as a stranger** (10 min). Open the site logged out. Every link opens, every page that shows a KPI
    says "simulated", and no page names a real client or any private person.
13. **Publish the access guide** (5 min). Upload `deliverables/docs/access-guide.docx` to the Drive folder, open it
    with Google Docs, then File → Save as Google Docs. It inherits the folder's sharing; check it opens in a
    private window.

## Things to confirm yourself

- Whether your ChatGPT account can create custom GPTs (step 8).
- Google's current file limits for Gem knowledge files (the pack uses two small files, so this is unlikely to bite).
- Whether Gemini Notebook is offered where you are. If not, attach these four PDFs to a chat with the Gem instead:
  the HKMA AML/CFT Guideline, the 2024 CDD circular, the 2019 AI principles and MAS Notice 626 (the Gem's file
  limit is unverified, so keep it to a few) [src:hkma-aml-cft-guideline-2023] [src:hkma-rba-cdd-2024]
  [src:hkma-ai-high-level-principles-2019] [src:mas-notice-626].
- Whether a Gem can be shared by link (the site uses screenshots meanwhile).
