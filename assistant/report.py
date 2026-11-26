"""The analyst's draft, and the gate that stops anything leaving without a person's approval.

Implements: assistant/one-step, assistant/human-approves, assistant/one-client-request

`markdown()` renders the draft review the analyst reads: every extracted value with the document and words it came
from, the ownership chain, each rule's flag with its reason, the one consolidated client request, and an empty
decision block. `write_draft()` saves it for the analyst. `release()` is the separate, later step and the only way
anything leaves: it reads the draft file the analyst ticked (and may have edited), refuses without an approval
and a name, and releases exactly the request text in that file, recording whether it was edited.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from assistant.rules import Result

LABELS = {"name": "Name", "registration_number": "Registration number", "jurisdiction": "Jurisdiction",
          "registered_address": "Registered address", "incorporation_date": "Incorporated"}
RULES = {"MISSING": "Missing", "STALE": "Out of date", "EXPIRED": "Expired", "MISMATCH": "Documents disagree",
         "UNRESOLVED": "Ownership unresolved", "UNVERIFIED": "Could not verify", "CHANGED": "Changed since last review",
         "NO_CHANGE": "No change"}


def markdown(r: Result, note: str = "") -> str:
    out = [f"# Draft KYC {'onboarding review' if r.case == 'onboarding' else 'periodic review'}: {r.pack}", "",
           "Drafted by the assistant for an analyst to approve, edit or reject. Fictional sample; nothing here is sent "
           "until an analyst approves it.", ""]
    if note:
        out += [f"_Model reply: {note}_", ""]
    out += ["## Entity", "", "| Field | Value | From |", "|---|---|---|"]
    for key, label in LABELS.items():
        if key in r.entity:
            f = r.entity[key]
            out.append(f"| {label} | {f['value']} | {f['doc']}: \"{f['quote']}\" |")
    out += ["", "## Ownership", ""]
    for h in r.ownership:
        out.append(f"- {h.owner} ({h.owner_type}) holds {h.percent:g}% of {h.owned}, per {h.doc}")
    out += ["", "Beneficial owners (more than 25%, through every chain):"]
    out += [f"- **{o.name}**: {o.percent:.1f}% via {' → '.join(reversed(o.path))}" for o in r.beneficial_owners] or ["- none found"]
    out += ["", "## Flags", "", "| Rule | Reason |", "|---|---|"]
    out += [f"| {RULES.get(f.rule, f.rule)} | {f.reason} |" for f in r.flags] or ["| — | No flags |"]
    out += ["", "## Client request", ""]
    if r.client_request:
        out += ["One message with every item, for the analyst to approve before it is sent:", "", "```text",
                r.client_request, "```"]
    else:
        out += ["Nothing to ask the client."]
    out += ["", "Edit the request above if needed, tick one box below, then run "
            "`uv run python -m assistant release <this file> --analyst \"<your name>\"`."]
    out += ["", "## Analyst decision", "", "- [ ] Approve as drafted", "- [ ] Edit, then approve", "- [ ] Reject (say why)",
            "", "Analyst: ____________   Date: ____________", ""]
    return "\n".join(out)


REQUEST = re.compile(r"```text\n(.*?)\n```", re.S)


def write_draft(r: Result, text: str, folder: Path) -> Path:
    """Save the draft for the analyst, with a sidecar recording the request as drafted (to tell edits apart)."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{r.pack}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    path.write_text(text, encoding="utf-8")
    drafted = REQUEST.search(text)
    path.with_suffix(".json").write_text(json.dumps({
        "pack": r.pack, "case": r.case,
        "request_sha256": hashlib.sha256((drafted.group(1) if drafted else "").encode()).hexdigest()}, indent=2))
    return path


def release(draft: Path, analyst: str, outbox: Path) -> Path:
    """Release exactly what the analyst approved in the draft file, as they left it. Refuses unless one approval
    box is ticked, Reject is not, and a named analyst releases it."""
    draft = Path(draft)
    text = draft.read_text(encoding="utf-8")
    ticked = {label for label in ("Approve as drafted", "Edit, then approve", "Reject")
              if re.search(rf"^- \[[xX]\] {re.escape(label)}", text, re.M)}
    if "Reject" in ticked or not ticked or not (analyst or "").strip():
        raise PermissionError("Nothing leaves the assistant without a named analyst's approval ticked in the draft.")
    meta = json.loads(draft.with_suffix(".json").read_text())
    found = REQUEST.search(text)
    request = found.group(1) if found else None
    edited = hashlib.sha256((request or "").encode()).hexdigest() != meta["request_sha256"]
    outbox = Path(outbox)
    outbox.mkdir(parents=True, exist_ok=True)
    path = outbox / f"{draft.stem}-released.json"
    path.write_text(json.dumps({"pack": meta["pack"], "approved_by": analyst.strip(), "decision": sorted(ticked),
                                "released_at": datetime.now().isoformat(timespec="seconds"), "edited": edited,
                                "client_request": request,
                                "outcome": "send client request" if request else "confirm no-change review"},
                               indent=2, ensure_ascii=False), encoding="utf-8")
    return path
