# Work items

One file per piece of work: `NNN-slug.md`, copied from `_template.md`. The `status:` line is the queue:

| Status | Means |
|---|---|
| `ready` | well formed, unblocked, nobody on it |
| `in-progress` | someone is on it |
| `in-review` | built, waiting for its review round |
| `blocked` | waiting on the owner or another item; "Questions" says which |
| `on-hold` | parked on purpose |
| `done` | merged, every box ticked |

`make check` fails on an item with a missing section, no boxes, an unknown status, or `done` with open boxes. Only
the owner rewrites acceptance boxes; agents tick them.
