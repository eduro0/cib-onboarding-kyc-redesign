<!-- Implements: package/roadmap, package/change-risks -->
# Change-risk register: AI-first onboarding and periodic KYC review

These are the ways the change could fail, and what keeps each failure small. Each risk has a likelihood and an
impact (High, Medium or Low), a mitigation built into the design or the rollout, the role that owns it, and an
early signal that shows it starting. The likelihood and impact ratings are judgments for an illustrative branch,
not measurements.

| # | Risk | Area | Likelihood | Impact | Mitigation | Owner | Early signal |
|--|----------|-----|-----|----|---------------|-------|----------|
| 1 | Analysts approve AI drafts without really checking them (automation bias) | Controls | High | High | Every fact shows its source words; seeded test packs with planted errors go into the queue; QC samples approved drafts | Head of onboarding operations | Approval time per draft drops below a few minutes; planted errors pass |
| 2 | A wrong extracted fact reaches the KYC file | Controls | Medium | High | Rules drop any fact whose quote isn't in the document; a person approves every change; pre-QC rule checks | Financial crime compliance | QC defects in AI-assisted files rise above baseline |
| 3 | Staff resist the change or fear for their jobs | Staff | Medium | Medium | Co-design the To-Be with analysts in Phase 0; say plainly that freed hours move to EDD and backlog; champions in each team | Head of onboarding operations | Low use of drafts in assist mode; analysts rebuild files by hand |
| 4 | Clients are confused by the new portal or request | Clients | Medium | Medium | Relationship managers brief clients first; email fallback during the pilot; feedback at each moment of truth | Head of corporate coverage | Portal drop-offs; more calls to relationship managers; complaints |
| 5 | Client data reaches a model provider outside approved terms | Technology | Low | High | Use only models the bank has approved for client data; send only the documents the step needs; log every call | Data protection officer | A call log entry to an unapproved endpoint |
| 6 | The supervisor sees the AI step as a black box | Regulators | Low | High | Human approval gates and an explanation on every flag, in line with the HKMA's principle that AI should be explainable [src:hkma-ai-high-level-principles-2019]; a named owner and an inventory entry for the AI use [src:hkma-speech-finance-ai-forum-2026]; the bank's own audit trail of every draft and decision; brief the supervisor before Phase 2 | Head of compliance | Questions in a supervisory review that the audit trail can't answer |
| 7 | The model changes or degrades after go-live | Technology | Medium | Medium | Pin model versions; rerun a fixed set of test packs before any change; monitor the share of drafts analysts edit | Model risk | Edit rate rises; the test-pack score falls |
| 8 | Complex structures (trusts, nominees, control without ownership) are handled as if simple | Controls | Medium | High | The rules find owners through shareholdings only and say so; any case with a trust, a nominee or management control goes to a manual path. AMLO's definition includes control as well as ownership [src:hk-amlo-sch2] | Financial crime compliance | A QC finding of a missed beneficial owner |
| 9 | Rules differ between Hong Kong and other Asia branches | Regulators | High | Medium | One rules configuration per jurisdiction; Singapore's MAS Notice 626 reviewed before any rollout there [src:mas-notice-626] | Regional compliance | A branch overrides the checklist by hand |
| 10 | The KPIs reward speed over quality | Controls | Medium | Medium | Report first-pass rate and QC defects next to cycle time, never cycle time alone; baselines measured in Phase 0 | Process engineering | Cycle time falls while defects or rework rise |
| 11 | A review with "no change" misses a real change | Controls | Low | High | No-change is confirmed by an analyst, never automatic; registry data refreshed before the check; trigger events start a review early [src:hkma-aml-cft-guideline-2023] | Financial crime compliance | A later trigger event reveals an older change |
| 12 | Client data crosses borders when other Asia branches join | Regulators | Medium | High | Run per-branch processing where data-transfer rules require; legal review of each branch's rules before Phase 3 | Data protection officer | A branch's files processed outside its approved location |
| 13 | The model provider fails, changes terms or becomes a concentration risk | Technology | Medium | Medium | Third-party and outsourcing risk review in Phase 0; a second approved model tested on the same packs; the manual process stays documented | Third-party risk | Provider incident, price or terms change |
| 14 | Shadow mode overloads analysts who also run today's process | Staff | Medium | Medium | Budget shadow time; shadow a sample, not every case; time-box each shadow window | Head of onboarding operations | Backlog grows during shadow weeks |

## How the register is used

The register is reviewed at each phase gate in the roadmap (`roadmap.md`). A risk whose early signal appears gets an
owner's action before the next phase starts. Risks 1, 2 and 8 are the ones that could create a regulatory finding,
so they are reported to compliance every month from Phase 1 on. Risks 5, 12 and 13 are reviewed with data protection and
third-party risk before Phase 0 closes.
