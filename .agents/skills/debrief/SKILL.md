---
name: debrief
description: Turn LESSONS.md and METRICS.md into fixes - a new rule, a new check or a skill edit. Use after a one-shot run, at the end of a project, or when the same mistake happens twice.
---

<!-- Implements: workflow/lessons-kept, workflow/measured -->

# Debrief

1. **Read** `LESSONS.md`, `METRICS.md` and every work item's "Questions" and "Log".
2. **For each lesson, choose the cheapest permanent fix,** in this order:
   1. a check in `checks/` (it can't be forgotten);
   2. a line in a skill (it's read every time that step runs);
   3. a line in `AGENTS.md`, only if it applies everywhere and can't be checked.

   Mark the lesson `→ fixed by <file>`.
3. **Read the numbers:** time per item, review findings found vs real, and items that needed the owner. Write three
   lines saying what helped, what was ceremony, and what to try next time.
