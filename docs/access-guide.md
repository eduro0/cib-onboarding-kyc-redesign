<!-- Implements: package/access-guide -->
# AI-first CIB onboarding and KYC review: where everything lives

This project redesigns two processes at an illustrative corporate and investment banking branch in Hong Kong:
corporate client onboarding and periodic KYC review. It maps both processes as they work today (As-Is) and as they
could work with AI drafting and people deciding (To-Be). It then models the gain on simulated cases, builds the AI
step as a prototype, and plans the rollout and its risks. Everything is built from public material. **Every KPI
figure is simulated**, and every company and person in the examples is fictional.

Start with the site. It tells the story in five pages and embeds or links every item below except the Drive
folder, which only this guide links. The deck, the KPI model, the documents and the maps sit in that one
Drive folder; the site, the dashboard and the notebook live in their own Google tools. Everything is shared as
"anyone with the link can view", so nothing needs a request for access. The one exception is the Gemini Notebook,
which asks for any Google sign-in.

## What each file is, and where its data comes from

| Item | Link | What it holds | Where its data comes from | Access |
|------|---|---------------|-------------|--------|
| **Site** | [Open](https://sites.google.com/view/ai-cib-onboarding-kyc) | The story in five pages: home, process maps, KPI model, roadmap and risks, sources | Embeds or links every item below except the Drive folder | Open, no sign-in |
| **Deck** | [Open](https://docs.google.com/presentation/d/1NY5-6Uw21y5usHQzzdbLTHQ_FRh0Z7PSBKmkxifX0x8/edit) | The whole project as a slide deck | Maps, KPI model and sources below; each slide with a figure names its source | Open, no sign-in |
| **As-Is map** | [Open](https://drive.google.com/file/d/1wXXFC0FDcoB-kqlbF-3hFQ3o3vch4mpH/view) | Today's process as a BPMN 2.0 file, with pain points and the client's moments of truth marked | Drawn from the public rules on the site's Sources page | Open, no sign-in |
| **To-Be map** | [Open](https://drive.google.com/file/d/1N1YpNn76IT5ud6A1vbZTImpZd9FampOp/view) | The redesigned process as a BPMN 2.0 file: AI steps are service tasks and human approval gates are user tasks. The map image in the Drive folder shows them in dashed purple and bold green | The As-Is map, redesigned | Open, no sign-in |
| **KPI model** | [Open](https://docs.google.com/spreadsheets/d/1k--UD5YGQmXXAJmpEZEnY5-w-UThYMkyqvxB2KsSEYI/edit) | A Google Sheet with five tabs: Read me, Assumptions, Cases, KPIs and Looker data | Simulated: every input is a labelled guess on the Assumptions tab | Open, no sign-in (view only) |
| **Assumptions** | [Open](https://docs.google.com/document/d/1BkMA0vu3ZBQs-jzgPxWuyB0PbTm1EeL6k7vaTJZGNsY/edit) | The reason behind every input to the KPI model, and how its outputs compare with published industry figures | Public sources where they exist; otherwise each input is marked as a judgment | Open, no sign-in |
| **Dashboard** | [Open](https://datastudio.google.com/reporting/3c983111-3061-493c-9199-728391efd9ff/page/TlJ0C) | One page of charts on the KPI model, As-Is against To-Be, with a case-type filter | Reads the KPI model's Looker data tab live | Open, no sign-in |
| **Roadmap** | [Open](https://docs.google.com/document/d/1Uysx6Ik9uvdcatLbLSwmeFg_7V2WVtUg7o3CLx4ppFE/edit) | The rollout in phases: what ships, who has to agree, and the KPI that decides the next phase | Public rules and the KPI model; sources listed at the end | Open, no sign-in |
| **Change-risk register** | [Open](https://docs.google.com/document/d/1qDkQZ2l80tYIhof_Q861swcpmlyejdpRgzo9syespOM/edit) | Risks to staff, clients, controls, regulators and technology, each with likelihood, impact, mitigation, owner and warning signal | Public rules and guidance; sources listed at the end | Open, no sign-in |
| **Gemini Notebook** | [Open](https://notebook.google.com/notebook/78afc557-d370-4c12-8e68-2e2b22e25b94) | The public rules the project relies on, loaded into one notebook so any claim can be checked against its source | The public sources on the site's Sources page | Google sign-in needed (any account) |
| **Drive folder** | [Open](https://drive.google.com/drive/folders/1B6jJKc8_NYIujZXAzjwmatOjkygWL0Sc) | This guide and the deck at the top; subfolders for the process maps (files and images), the KPI model and its assumptions, the roadmap and risks, and the assistant's draft and screenshots | Same as each file | Open, no sign-in |

## How the numbers flow

The KPI figures follow one path, so a number on the dashboard can be traced back to the guess behind it:

1. **Assumptions tab.** Every input (time spent on each step, waiting time between steps, how often a client's pack arrives incomplete) is a labelled
   guess. None of it is real bank data. The Assumptions document gives the reason for each one.
2. **Cases tab.** A script walks a simulated year of <!-- check: onb_cases_as_is = 300 -->300 onboardings and
   <!-- check: rev_cases_as_is = 700 -->700 periodic reviews through both maps, one row per case (simulated).
3. **KPIs tab.** Live formulas average the Cases tab by process and case type, next to the values the script
   computed, so the two can be compared.
4. **Looker data tab.** The same cases in long form, one row per case and KPI, which is the shape the dashboard
   reads.
5. **Dashboard.** Data Studio, Google's free dashboard tool (called Looker Studio until April 2026)
   [src:data-studio-sheets-free], reads the Looker data tab directly. If the Sheet changes, the dashboard follows.

## The assistant

The To-Be map's AI step is built as a working assistant and tried on fictional client packs. It is not on the
site; two versions exist:

- **A Python prototype.** The model only extracts facts with their exact source words. Fixed rules decide what is
  missing and what changed, and nothing reaches the client until an analyst approves it. The Drive folder holds a
  draft it produced.
- **A Gemini skill.** The same checklist set up in Google's Gemini (Google renamed Gems to skills
  [src:gemini-gems-now-skills]). Here the model does the checking itself. The Drive folder holds
  screenshots of its answer, because the skill itself is not shared publicly.

## The code behind it

Everything above except the hand-built Google tools is generated by code: the simulation, the map files and their
images, the workbook, the deck and the documents, from one repository with a single build command. Automated
checks fail the build if any figure in the deck or the documents differs from the model's output, if a passage that
names a regulator cites no recorded source, or if a page showing a KPI does not say it is simulated. The assistant prototype and
its tests sit in the same repository. The repository is public and open source (MIT licence): **github.com/eduro0/cib-onboarding-kyc-redesign**.

## Opening the files

- **The maps** are BPMN 2.0 files. Drive can't draw them; to see the diagram, download the file and open it at
  <https://demo.bpmn.io>, or use the PNG images in the Drive folder.
- **The KPI model** opens view-only. To try other assumptions, use File → Make a copy and change the Assumptions
  tab in your copy; its KPIs tab recalculates.
- **The dashboard** filters by case type with the drop-down at the top. It starts on onboarding; the on-time chart
  fills in when you choose `review`, the only case type with a deadline.
