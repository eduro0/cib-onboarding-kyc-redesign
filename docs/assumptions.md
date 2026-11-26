<!-- Implements: kpi-model/assumptions-justified -->
# Why the KPI model's assumptions are what they are

The KPI model walks a simulated year of cases through the As-Is and To-Be maps. Every input is a guess written down
so it can be argued with: no bank's internal data was used, and **every figure here is simulated**. This document
gives the reasoning behind each input, step by step, and then checks the model's outputs against published
industry figures. The inputs are guesses; comparing the outputs with published ranges shows whether the guesses
add up to something realistic.

## What the model covers, and what it leaves out

The model counts KYC work only: requesting and checking documents, building the KYC file, tracing owners,
screening, rating, enhanced due diligence, quality control and sign-off. A real corporate onboarding also includes
credit approval, legal documentation and account and product set-up, which the redesign does not touch. So the
onboarding figures are the KYC part of onboarding, not the whole of it.

Touch time is staff hours of hands-on work. Elapsed time is calendar days, queues included. A gateway share is the
proportion of cases taking a branch, such as the share of packs found incomplete.

## Why a periodic review costs as much staff time as an onboarding

In this model a periodic review takes slightly more hands-on time per case than the KYC part of an onboarding:
<!-- check: rev_touch_hours_as_is = 20.9 -->20.9 hours against <!-- check: onb_touch_hours_as_is = 19.2 -->19.2
(simulated). That is deliberate, for three reasons.

1. **Today, a review rebuilds the file.** The As-Is map sends a review through the same steps as an onboarding:
   request documents, check the pack, re-key the data, trace the owners, screen, rate and quality-check. That is
   the pain point the redesign attacks: each review restarts from scratch even when nothing changed. Industry
   surveys back the weight of reviews: US investment banks reported a mean of 82 days per KYC review in 2023
   [src:fenergo-kyc-trends-2023-global], and medium-risk reviews can take four to five months at US mid-market
   commercial banks [src:fenergo-commercial-banking-us-2024].
2. **A review has two steps an onboarding does not.** Pulling the old file and listing what is stale at the start,
   and recording the outcome and the next review date at the end. An onboarding has only the business sign-off
   instead.
3. **The redesign helps reviews more.** Many reviews find nothing has changed, and in the To-Be design the analyst
   confirms that instead of asking the client for everything again. That is why reviews gain more than onboardings.

Across the year, reviews take far more staff time than onboardings: <!-- check: rev_staff_hours_year_as_is = 14659 -->14,659
hours against <!-- check: onb_staff_hours_year_as_is = 5774 -->5,774 (simulated). That is mostly volume, not effort
per case: the model assumes <!-- check: rev_cases_as_is = 700 -->700 reviews a year against
<!-- check: onb_cases_as_is = 300 -->300 new clients. With review cycles of one, three or five years by risk tier
[src:ey-kyc-refresh-2024], a branch re-reviews a large part of its existing book every year, while new clients add
only a little to it.

## How the outputs compare with published figures

The model's As-Is outputs (simulated) against public benchmarks:

- **Onboarding cycle time.** The model gives <!-- check: onb_cycle_days_as_is = 63.6 -->63.6 days on average
  (simulated). Banks reported 30 days on average in 2017 [src:thomson-reuters-kyc-2017-globaltreasurer], while UK
  corporate banks now report more than six weeks [src:fenergo-fincrime-trends-2025]. The model sits above both
  because it includes the client's time to send documents and every chase. That matches what corporates say: 30%
  reported onboarding taking more than two months [src:thomson-reuters-kyc-2016]. The model has
  <!-- check: onb_over_60_days_as_is = 0.42 -->42% of onboardings over 60 days (simulated), so it leans to the slow
  side of that figure.
- **Review cycle time.** The model gives <!-- check: rev_cycle_days_as_is = 61.1 -->61.1 days (simulated), between a
  global average of 20 days for refreshing a client record in 2017 [src:thomson-reuters-kyc-2017-globaltreasurer]
  and 82 days per review at US investment banks in 2023 [src:fenergo-kyc-trends-2023-global].
- **Staff hours per review.** The model's As-Is review takes <!-- check: rev_touch_hours_as_is = 20.9 -->20.9
  hands-on hours per case (simulated). A PwC study of periodic reviews at banks in Singapore found 18.5 hours for a
  corporate with a simple structure, 40.3 for a typical one and 62 for a complex one [src:pwc-sg-pkyc-2022]. The
  model sits at the simple end, mostly because it gives quality control far less time than PwC's four-eye review.
  A lighter As-Is makes the gain smaller, not larger, so the model leans conservative here.
- **Client touches.** The model counts separate requests to the client, about two per case
  (<!-- check: onb_client_touches_as_is = 1.93 -->1.93 for onboarding, simulated). Corporates report eight
  interactions with the bank per onboarding [src:thomson-reuters-kyc-2016] and banks report four
  [src:thomson-reuters-kyc-2017-globaltreasurer]. Those counts include every call and email; the model counts only
  formal document requests, so it is lower by design.

## How much of the gain depends on the guesses

The To-Be gain comes from two kinds of input: less hands-on work (AI drafts, people check) and shorter queues. The
queues are the weaker guess, so the model reruns the To-Be map with today's queue times. Onboarding then takes
<!-- check: onb_cycle_days_to_be_slow_queues = 47.7 -->47.7 days instead of
<!-- check: onb_cycle_days_to_be = 36.1 -->36.1, and reviews <!-- check: rev_cycle_days_to_be_slow_queues = 31.4 -->31.4
instead of <!-- check: rev_cycle_days_to_be = 22.1 -->22.1 (all simulated). Most of the gain survives with no
faster queues at all. The inputs to test first in a real pilot are the analyst's time to check an AI draft, the
share of reviews that need nothing from the client, and the share of packs still incomplete.

## Every input, step by step

Values are as the model uses them; each case varies around them (see the run settings). Hours are staff hands-on
time per case; days are elapsed calendar days, queue included.

<!-- assumption steps -->
