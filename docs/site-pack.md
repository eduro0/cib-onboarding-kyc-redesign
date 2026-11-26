<!-- Implements: package/site-pack -->
# Google Sites pack: one page that links everything

The site is the single link to share, so it opens with the story in a few lines and puts every deliverable one
click away. Any personal Google account can create and publish a site [src:google-sites-help]. Allow 45–60
minutes once the files are in Drive (`docs/owner-checklist.md` steps 1–6).

Theme: "Simple" or "Vision", one accent colour (blue). Site name: "AI-first CIB onboarding & KYC review".
Footer on every page: "Portfolio piece by Eduard Rodriguez Lopez, built from public material. All KPI figures
are simulated; all companies and people in the examples are fictional."

## Page 1: Home

**Heading:** AI-first redesign of corporate client onboarding and periodic KYC review

**Text:** Corporate onboarding is slow, and clients notice every extra ask. This project maps the process at an
illustrative corporate and investment banking branch in Hong Kong (As-Is), redesigns it so AI reads and drafts
while people decide (To-Be), models the gain on simulated cases, builds the AI step as a working prototype, and
plans the rollout and its risks.

**Insert:** the deck (Insert → Slides → the Google Slides copy of `deck.pptx`). Buttons to pages 2–5.

## Page 2: Process maps

**Text:** Both maps are BPMN 2.0 files that open in bpmn.io or Camunda Modeler. Red badges are pain points, amber
badges the client's moments of truth, dashed purple steps are AI, and bold green steps are human approval gates.

**Insert:** images `deliverables/maps/as-is.png` and `deliverables/maps/to-be.png` (upload to Drive). Links to
`as-is.bpmn` and `to-be.bpmn` in Drive (viewer access).

## Page 3: KPI model

**Text:** The KPI model walks a simulated year of <!-- check: onb_cases_as_is = 300 -->300 onboardings and
<!-- check: rev_cases_as_is = 700 -->700 periodic reviews through both maps. Every input is a labelled guess on the
Assumptions tab, and a sensitivity run shows how much of the gain depends on shorter queues.

**Text (second paragraph):** The dashboard is built in Data Studio, Google's free dashboard tool, called Looker
Studio until April 2026 [src:data-studio-sheets-free].

**Insert:** the Data Studio report (Insert → Embed → the embed URL from `docs/dashboard-guide.md` step 4). A
link to the Google Sheets copy of `kpi-model.xlsx`.

## Page 4: Roadmap and risks

**Insert:** the Google Docs copies of `roadmap.docx` and `change-risks.docx` (Insert → Docs).

## Page 5: Sources

**Text:** The rules and outside figures come from public sources, listed below; each was checked against its
exact wording on 18 November 2026. The KPI figures are simulated and sourced to nothing outside the model.

**Insert:** the Gemini Notebook link (`docs/notebook-pack.md`), and a short list of the main sources: AMLO
Schedule 2, the HKMA AML/CFT Guideline, the HKMA circulars on CDD and on AI, MAS Notice 626 [src:hk-amlo-sch2]
[src:hkma-aml-cft-guideline-2023] [src:hkma-rba-cdd-2024] [src:hkma-ai-high-level-principles-2019] [src:mas-notice-626].

## Publish

Publish → web address `ai-cib-onboarding-kyc` (or similar) → visible to "Anyone". Check every page as a
logged-out visitor before sharing the link.
