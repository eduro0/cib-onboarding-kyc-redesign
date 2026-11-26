<!-- Implements: package/roadmap, package/change-risks -->
# Implementation roadmap: AI-first onboarding and periodic KYC review

The redesign should be rolled out in four phases. The order runs from the least client-facing change to the most,
and from the lowest-risk clients to the highest, so each phase proves something before the next one depends on it.
Every new AI step runs in shadow first: it drafts alongside the analysts, who keep working as today, until its
accuracy is measured. Each phase ends at a gate, a short list of measured results that decides whether the next
phase starts. The KPI targets below come from the simulated model (`kpi-model.xlsx`). They are simulated
estimates to replace with measured baselines in Phase 0, not commitments.

## Phase 0: Measure and agree (weeks 0–6)

**What ships.** A measured As-Is baseline and an agreed design, before anything is built.

- Time 40–60 real files end to end (onboarding and periodic review) to replace the model's guessed inputs.
- Walk the As-Is and To-Be maps with operations, compliance, relationship managers and QC, and correct them.
- Agree one definition per KPI (cycle time, touch time, first-pass rate, rework, client touches, reviews on time).
- Agree with compliance which steps stay human approval gates. The design keeps a person in control of every AI
  output that changes a client's file, rating or status, in line with the HKMA's principle that banks stay
  accountable for AI-driven decisions and use controls such as a human-in-the-loop mechanism
  [src:hkma-ai-high-level-principles-2019].
- Name an owner for the AI use and enter it in the bank's inventory of AI applications, which the HKMA's 2026
  guidance calls for, as described by the HKMA [src:hkma-speech-finance-ai-forum-2026].
- Data protection, information security and third-party risk review of the model provider before any client
  document reaches it.

**Who agrees.** Head of client onboarding operations, financial crime compliance, model risk, data protection,
information security.

**Gate to Phase 1.** Baseline KPIs signed off; gates agreed in writing; no open objection from model risk, data
protection or third-party risk.

## Phase 1: Shadow, then assist, on low- and medium-risk periodic reviews (weeks 6–16)

**What ships.** AI pre-fill and pack reading for periodic reviews, with no change the client can see.

- Weeks 6–10, **shadow mode**: the assistant drafts each review in parallel while analysts work as they do today.
  Compare its drafts with the analysts' files. Budget the extra analyst time this takes.
- Weeks 10–16, **assist mode**: analysts start from the draft. Every extracted fact shows the exact words it came
  from; facts the assistant can't trace are dropped and flagged.
- Reviews with nothing changed and nothing expired are confirmed without contacting the client, as the HKMA asks
  banks not to request information they already hold [src:hkma-rba-cdd-2024].
- Update the KYC procedure for assisted reviews, and train the analysts and QC reviewers who use it.

**Why reviews first.** They are numerous and repetitive, the bank already holds a file to check the AI against,
and the client sees no new interface.

**Who agrees.** Head of client onboarding operations (go-live of assist mode), financial crime compliance
(procedure change), model risk (shadow results).

**Gate to Phase 2.**

- Extraction accuracy on sampled shadow cases meets the target agreed in Phase 0.
- No AI output reached a file without approval (audit trail check).
- Review touch time falls against the measured baseline. The model's simulated estimate is from
  <!-- check: rev_touch_hours_as_is = 20.9 -->20.9 to <!-- check: rev_touch_hours_to_be = 7.8 -->7.8 staff hours per review.
- QC defect rate no worse than baseline; analysts and QC trained.

## Phase 2: Onboarding with one consolidated request (months 4–8)

**What ships.** The client-facing redesign for new corporate clients.

- Four weeks of shadow mode first for the two new AI steps, onboarding pre-fill and screening-hit triage, each
  with its own accuracy gate.
- A tailored document list per entity type, pre-filled from registries, sent as one request and uploaded once.
- Screening-hit triage: the assistant explains each hit, and the analyst decides.
- Relationship managers brief their clients before go-live, with email as a fallback channel during the pilot.
- Brief the supervisor before the client-facing change goes live.

**Who agrees.** Head of corporate coverage (client impact), financial crime compliance, information security and
IT (client portal), operational risk, model risk (the new AI steps).

**Gate to Phase 3.**

- Onboarding cycle time falls against the measured baseline. The model's simulated estimate is from
  <!-- check: onb_cycle_days_as_is = 63.6 -->63.6 to <!-- check: onb_cycle_days_to_be = 36.1 -->36.1 days, or to
  <!-- check: onb_cycle_days_to_be_slow_queues = 47.7 -->47.7 days if queues stay as long as today.
- First-pass rate rises. Simulated: from <!-- check: onb_first_pass_as_is = 0.38 -->38% to <!-- check: onb_first_pass_to_be = 0.62 -->62%,
  up <!-- check: onb_first_pass_change_pts = 24 -->24 points.
- Client feedback at the three moments of truth (first request, being asked again, accounts live) is no worse,
  and complaints are flat or down.

## Phase 3: High-risk support, pre-QC and scale-out (months 8–12)

**What ships.**

- Drafted enhanced-due-diligence memos for compliance to review. Senior-management approval of high-risk
  relationships stays as it is [src:hkma-aml-cft-guideline-2023].
- Pre-QC rule checks before human sign-off.
- Event-driven reviews: a change in beneficial ownership or control starts a review, which the HKMA guideline
  names as a trigger event [src:hkma-aml-cft-guideline-2023].
- A rules configuration per jurisdiction, starting with Singapore, where MAS Notice 626 sets its own CDD and
  review requirements [src:mas-notice-626] [src:mas-guidelines-notice-626]. Client data stays where the
  branch's data-transfer rules require.
- Model monitoring in production: drift on a fixed test set of packs, and the share of drafts analysts edit.
- Where the data supports it, consider sampling instead of approving every low-risk draft. The HKMA describes a
  progressive shift from "human-in-the-loop" to "human-on-the-loop" oversight with clear accountability and
  monitoring [src:hkma-speech-finance-ai-forum-2026]; this design starts fully in the loop.

**Who agrees.** The senior manager who approves high-risk relationships (EDD memos), model risk (monitoring),
regional compliance and the Singapore branch (rules configuration), data protection (cross-border data).

**Gate to steady state.** Reviews on time rise against baseline (simulated: from
<!-- check: rev_on_time_as_is = 0.87 -->87% to <!-- check: rev_on_time_to_be = 1.0 -->100%), with no rise in QC defects
or regulatory findings.

## What the simulated model says the full redesign is worth

Across simulated volumes of <!-- check: onb_cases_as_is = 300 -->300 onboardings and
<!-- check: rev_cases_as_is = 700 -->700 reviews a year at one branch, the model frees about
<!-- check: staff_hours_year_saved = 12134 -->12134 staff hours a year, about <!-- check: fte_saved = 7.6 -->7.6
full-time staff, to move to enhanced due diligence and backlog. All of this is simulated: every input is a
labelled guess in the Assumptions tab, so Phase 0's measured baseline replaces it.
