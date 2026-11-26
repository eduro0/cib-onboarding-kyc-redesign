"""The deterministic half of the assistant: everything that decides.

Implements: assistant/llm-reads-rules-decide, assistant/one-client-request, assistant/one-step

The model's extraction is treated as a claim, not a fact. A fact is kept only if its quote is found word for word
in the document it names AND the quote itself contains what is claimed (the value, the name, the percentage);
anything else becomes an UNVERIFIED flag for the analyst. Document types, subjects and dates are read by rules
from each document's own header, not taken from the model. From the kept facts, fixed rules work out:
- beneficial owners, by multiplying shareholdings along each ownership chain (more than 25%, as in AMLO
  Schedule 2), and any chain that stops at a company with no ownership evidence (UNRESOLVED);
- for onboarding: documents missing for the entity, each director and each beneficial owner (MISSING), proofs of
  address older than the policy window (STALE), expired documents (EXPIRED), and directors listed differently by
  different documents (MISMATCH);
- for a periodic review: what changed against the bank's file (CHANGED), what that change makes necessary, and
  NO_CHANGE only when directors, shareholders, name and address were all re-read and verified and match the file
  (otherwise NOT_CONFIRMED);
- NO_OWNER when nobody passes the threshold (the person exercising control must then be identified),
  CONTROL_CHECK when a person holds a majority of a company in the chain, and an ask for incorporation evidence of
  every intermediate company.
Every flag that needs something from the client carries the wording of that ask, and all asks are joined into one
client request. Model opinions (risk views, recommendations) are never read.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

REQUIREMENTS = yaml.safe_load((Path(__file__).parent / "requirements.yaml").read_text(encoding="utf-8"))
BO_THRESHOLD = REQUIREMENTS["beneficial_owner_threshold_percent"]
ADDRESS_WINDOW = REQUIREMENTS["proof_of_address_max_age_days"]


@dataclass
class Flag:
    rule: str
    reason: str
    evidence: str = ""
    ask: str | None = None

    @property
    def asks_client(self) -> bool:
        return self.ask is not None


@dataclass
class Holding:
    owner: str
    owner_type: str
    owned: str
    percent: float
    doc: str
    quote: str


@dataclass
class Owner:
    name: str
    percent: float
    path: list[str]


@dataclass
class Result:
    pack: str
    case: str
    entity: dict
    directors: dict[str, list[str]]
    ownership: list[Holding]
    beneficial_owners: list[Owner]
    documents: list[dict]
    flags: list[Flag] = field(default_factory=list)
    client_request: str | None = None


def norm(text: str) -> str:
    """Compare names and quotes case- and punctuation-insensitively."""
    return re.sub(r"\s+", " ", re.sub(r"[^\w%]+", " ", text.lower())).strip()


def same(a: str, b: str) -> bool:
    return norm(a) == norm(b)


def load_docs(folder: Path) -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(folder.glob("*.txt"))}


COMPANY_WORDS = re.compile(r"\b(ltd|limited|pte|inc|llc|corp|corporation|plc|gmbh|holdings|company|co)\b", re.I)
DOC_TYPES = [("certificate of incorporation", "certificate_of_incorporation"), ("business registration", "business_registration"),
             ("articles of association", "articles_of_association"), ("register of directors", "register_of_directors"),
             ("annual return", "annual_return"), ("register of members", "register_of_members"),
             ("significant controllers", "significant_controllers_register"), ("company particulars", "registry_extract"),
             ("registry extract", "registry_extract"), ("passport", "id_document"), ("identity card", "id_document"),
             ("proof of address", "proof_of_address"), ("utility bill", "proof_of_address")]


def in_quote(quote: str, doc_text: str) -> bool:
    """The quote is long enough to mean something and appears word for word (case and punctuation aside)."""
    q = norm(quote or "")
    return len(q) >= 8 and q in norm(doc_text)


def percents(text: str) -> set[float]:
    return {float(m) for m in re.findall(r"(?<![\d.])(\d+(?:\.\d+)?)\s*%", text)}


def check_fact(kind: str, fact: dict, docs: dict[str, str]) -> str | None:
    """None if the fact is supported by its own quote; otherwise the reason it isn't."""
    doc = fact.get("doc")
    if doc not in docs:
        return f"names {doc}, which isn't in the pack"
    if not in_quote(fact.get("quote", ""), docs[doc]):
        return f"its quote isn't in {doc}"
    q = norm(fact["quote"])
    if kind == "entity" and norm(str(fact.get("value", ""))) not in q:
        return "the quote doesn't contain the value"
    if kind == "director" and norm(fact.get("name", "")) not in q:
        return "the quote doesn't contain the name"
    if kind == "ownership":
        if norm(fact.get("owner", "")) not in q:
            return "the quote doesn't contain the owner"
        if float(fact.get("percent", -1)) not in percents(fact["quote"]):
            return f"the quote doesn't state {fact.get('percent')}%"
        if norm(fact.get("owned", "")) not in norm(docs[doc]):
            return f"{doc} doesn't mention {fact.get('owned')}"
    return None


def read_header(name: str, text: str) -> dict | None:
    """Type, subject, date and expiry of a document, from its own header lines; None if it has no DOCUMENT line."""
    fields = dict(re.findall(r"^([A-Za-z ]+):\s*(.+)$", text, re.M))
    title = fields.get("DOCUMENT", "").lower()
    if not title:
        return None
    kind = next((t for key, t in DOC_TYPES if key in title), "other")
    subject = fields.get("NAME") or fields.get("COMPANY") or fields.get("Business name") or ""
    subject = re.split(r",| company number", subject)[0].strip()
    expiry = fields.get("VALID UNTIL") or fields.get("DATE OF EXPIRY")
    return {"file": name, "type": kind, "subject": subject or None, "date": fields.get("DATE") or fields.get("DATE OF ISSUE"),
            "expiry": expiry}


def parse_date(value: str | None) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


def chains(target: str, holdings: list[Holding]) -> tuple[list[Owner], list[str]]:
    """People's effective ownership of `target`, and companies in the chain with no ownership evidence."""
    owners: dict[str, Owner] = {}
    unresolved: list[str] = []

    def walk(company: str, share: float, path: list[str]) -> None:
        for h in (h for h in holdings if same(h.owned, company)):
            eff = share * h.percent / 100
            if h.owner_type == "person":
                key = norm(h.owner)
                prev = owners.get(key)
                owners[key] = Owner(h.owner, (prev.percent if prev else 0) + eff * 100, path + [h.owner])
            elif any(same(x.owned, h.owner) for x in holdings) and h.owner not in path:
                walk(h.owner, eff, path + [h.owner])
            else:
                unresolved.append(h.owner)

    walk(target, 1.0, [target])
    return sorted(owners.values(), key=lambda o: -o.percent), unresolved


def has_doc(documents: list[dict], kinds: list[str], subject: str | None = None) -> list[dict]:
    return [d for d in documents if d.get("type") in kinds and (subject is None or same(d.get("subject") or "", subject))]


def evaluate(folder: Path, extraction: dict, as_of: date) -> Result:
    folder = Path(folder)
    docs = load_docs(folder)
    bank_path = folder / "bank-file.json"
    bank = json.loads(bank_path.read_text()) if bank_path.exists() else None
    flags: list[Flag] = []

    entity = {}
    for key, fact in (extraction.get("entity") or {}).items():
        why = check_fact("entity", fact, docs)
        if why is None:
            entity[key] = fact
        else:
            flags.append(Flag("UNVERIFIED", f"Entity field '{key}' dropped: {why}. Check it by hand.", str(fact.get("quote"))))
    directors: dict[str, list[str]] = {}
    for m in extraction.get("director_mentions") or []:
        why = check_fact("director", m, docs)
        if why is None:
            directors.setdefault(m["doc"], []).append(m["name"])
        else:
            flags.append(Flag("UNVERIFIED", f"Director '{m.get('name')}' dropped: {why}.", str(m.get("quote"))))
    holdings = []
    for o in extraction.get("ownership") or []:
        why = check_fact("ownership", o, docs)
        if why is None:
            kind = "company" if COMPANY_WORDS.search(o["owner"]) else "person"  # decided by rule, not by the model
            holdings.append(Holding(o["owner"], kind, o["owned"], float(o["percent"]), o["doc"], o["quote"]))
        else:
            flags.append(Flag("UNVERIFIED", f"Shareholding of '{o.get('owner')}' dropped: {why}.", str(o.get("quote"))))
    documents = []
    claimed = {d.get("file"): d for d in extraction.get("documents") or []}
    for name, text in docs.items():
        header = read_header(name, text)
        if header is None:
            flags.append(Flag("UNVERIFIED", f"{name} has no document header, so its type can't be confirmed; check it by hand."))
            continue
        documents.append(header)
        model = claimed.get(name)
        if model and model.get("type") != header["type"]:
            flags.append(Flag("UNVERIFIED", f"The model called {name} a {model.get('type')}; its header says {header['type']}. The header is used."))

    target = (entity.get("name") or {}).get("value") or (bank or {}).get("entity", {}).get("name", folder.name)
    all_directors = sorted({norm(n): n for names in directors.values() for n in names}.values())
    beneficial, unresolved = chains(target, holdings)
    beneficial = [o for o in beneficial if o.percent > BO_THRESHOLD]
    for company in unresolved:
        flags.append(Flag("UNRESOLVED", f"The ownership chain stops at {company}: no evidence of who owns it.",
                          ask=f"Register of members (or an ownership chart signed by a director) for {company}"))
    for company in {h.owned for h in holdings}:
        total = sum(h.percent for h in holdings if same(h.owned, company))
        if 0 < total < 99.5:
            flags.append(Flag("UNRESOLVED", f"Only {total:g}% of {company} is accounted for by verified shareholdings.",
                              ask=f"Complete register of members of {company}"))
        for h in holdings:
            if same(h.owned, company) and h.owner_type == "person" and h.percent > 50 and not same(company, target):
                stake = sum(x.percent for x in holdings if same(x.owner, company))
                flags.append(Flag("CONTROL_CHECK", f"{h.owner} holds {h.percent:g}% of {company}, which holds {stake:g}% of "
                                                   f"{target}: check whether {h.owner} controls that whole stake."))
    if holdings and not beneficial:
        flags.append(Flag("NO_OWNER", f"No individual owns more than {BO_THRESHOLD}% of {target}, so the person exercising "
                                      "control must be identified (HKMA AML/CFT Guideline para 4.4.9).",
                          ask=f"Details of the individual(s) who control {target}, or its senior managing official, with an identity document for each"))

    case = "review" if bank else "onboarding"
    if case == "onboarding":
        flags += onboarding_flags(target, documents, directors, all_directors, beneficial, as_of)
        for company in sorted({h.owner for h in holdings if h.owner_type == "company"}):
            if not has_doc(documents, ["certificate_of_incorporation", "registry_extract"], company):
                flags.append(Flag("MISSING", f"No evidence that {company}, which owns part of the chain, exists as stated.",
                                  ask=f"Certificate of incorporation (or a registry extract) of {company}"))
    else:
        flags += review_flags(target, bank, entity, documents, directors, all_directors, holdings, beneficial, unresolved,
                              as_of, flags)

    result = Result(folder.name, case, entity, directors, holdings, beneficial, documents, flags)
    result.client_request = client_request(target, flags, case)
    return result


def person_flags(people: dict[str, str], documents: list[dict], as_of: date, check_age: bool) -> list[Flag]:
    flags = []
    for name, role in people.items():
        if not has_doc(documents, ["id_document"], name):
            flags.append(Flag("MISSING", f"No identity document for {name} ({role}).",
                              ask=f"Identity document (passport or ID card) for {name} ({role})"))
        addresses = has_doc(documents, ["proof_of_address"], name)
        if not addresses:
            flags.append(Flag("MISSING", f"No proof of address for {name} ({role}).",
                              ask=f"Proof of address for {name} ({role}), dated within the last {ADDRESS_WINDOW // 30} months"))
        elif check_age:
            newest = max(parse_date(a.get("date")) or date.min for a in addresses)
            if (as_of - newest).days > ADDRESS_WINDOW:
                flags.append(Flag("STALE", f"Proof of address for {name} is dated {newest}, older than {ADDRESS_WINDOW} days.",
                                  ask=f"A recent proof of address for {name}, dated within the last {ADDRESS_WINDOW // 30} months"))
    return flags


def expired(documents: list[dict], as_of: date) -> list[Flag]:
    out = []
    for d in documents:
        exp = parse_date(d.get("expiry"))
        if exp and exp < as_of:
            out.append(Flag("EXPIRED", f"{d['file']} expired on {exp}.", ask=f"A current {d['type'].replace('_', ' ')} for {d.get('subject')}"))
    return out


def onboarding_flags(target, documents, directors, all_directors, beneficial, as_of) -> list[Flag]:
    flags = []
    for req in REQUIREMENTS["onboarding"]["entity"]:
        if not has_doc(documents, req["any_of"]):
            flags.append(Flag("MISSING", f"No {req['name']} for {target}.", ask=f"{req['name'][0].upper()}{req['name'][1:]} of {target}"))
    listing = {doc: {norm(n) for n in names} for doc, names in directors.items()}
    if len(listing) > 1 and len({frozenset(v) for v in listing.values()}) > 1:
        for name in all_directors:
            missing_from = [doc for doc, names in listing.items() if norm(name) not in names]
            if missing_from:
                flags.append(Flag("MISMATCH", f"{name} is listed as a director in some documents but not in {', '.join(missing_from)}.",
                                  ask=f"Confirmation of whether {name} is a current director, with an updated register of directors"))
    people = {n: "director" for n in all_directors}
    for o in beneficial:
        people[o.name] = "director and beneficial owner" if o.name in people else "beneficial owner"
    flags += person_flags(people, documents, as_of, check_age=True)
    flags += expired(documents, as_of)
    return flags


def review_flags(target, bank, entity, documents, directors, all_directors, holdings, beneficial, unresolved, as_of,
                 earlier: list[Flag]) -> list[Flag]:
    flags, on_file = [], bank.get("documents_on_file", [])
    combined = on_file + documents
    old_directors = {norm(n) for n in bank.get("directors", [])}
    new_directors = [n for n in all_directors if norm(n) not in old_directors]
    gone = [n for n in bank.get("directors", []) if norm(n) not in {norm(x) for x in all_directors}]
    old_own = {norm(o["owner"]): o["percent"] for o in bank.get("ownership", []) if same(o["owned"], target)}
    new_own = {norm(h.owner): h.percent for h in holdings if same(h.owned, target)}
    changes = []
    if new_directors:
        changes.append(f"new director(s): {', '.join(new_directors)}")
    if gone:
        changes.append(f"director(s) no longer listed: {', '.join(gone)}")
    names = {norm(o["owner"]): o["owner"] for o in bank.get("ownership", [])} | {norm(h.owner): h.owner for h in holdings}
    if new_own and new_own != old_own:
        changes.append("shareholding changed: " + "; ".join(
            f"{names[k]} {old_own.get(k, 0):g}% → {new_own.get(k, 0):g}%" for k in names
            if old_own.get(k, 0) != new_own.get(k, 0)))
    addr = (entity.get("registered_address") or {}).get("value")
    if addr and not same(addr, bank["entity"].get("registered_address", "")):
        changes.append(f"registered address changed to {addr}")
    for c in changes:
        flags.append(Flag("CHANGED", f"Since the last review: {c}. Refresh the affected items and re-screen."))
    if new_own and new_own != old_own:
        flags.append(Flag("MISSING", f"Ownership changed, so the significant controllers register on file is out of date.",
                          ask=f"Updated significant controllers register of {target}"))
    people = {n: "new director" for n in new_directors}
    old_bos = {norm(o["owner"]) for o in bank.get("ownership", []) if o["percent"] > BO_THRESHOLD}
    for o in beneficial:
        if norm(o.name) not in old_bos:
            people[o.name] = "new beneficial owner"
    flags += person_flags(people, combined, as_of, check_age=False)
    flags += expired(combined, as_of)
    gaps = [label for label, ok in (("directors", bool(directors)), ("shareholders", bool(new_own)),
                                    ("registered address", "registered_address" in entity), ("name", "name" in entity)) if not ok]
    if any(f.rule == "UNVERIFIED" for f in earlier):
        gaps.append("facts that could not be verified")
    if gaps:
        flags.append(Flag("NOT_CONFIRMED", "Can't confirm the file is current: no verified " + ", ".join(gaps)
                          + " in this pack. The analyst checks these against the registry by hand."))
    elif not changes and not unresolved and not any(f.asks_client for f in flags):
        flags.append(Flag("NO_CHANGE", "Directors, shareholders, name and address were re-read from the registry and "
                                       "match the file, and no expiry is recorded on file. Proofs of address were not "
                                       "re-checked. The analyst can confirm a no-change review without contacting the client."))
    return flags


def client_request(target: str, flags: list[Flag], case: str = "onboarding") -> str | None:
    """One message with every ask, de-duplicated, or None when nothing is needed from the client."""
    asks = list(dict.fromkeys(f.ask for f in flags if f.asks_client))
    if not asks:
        return None
    lines = [f"Dear {target} team,", "",
             ("Thank you for your documents. To complete our review we need the following items. "
              if case == "onboarding" else
              "It is time for our regular review of your account file. We have checked the public registry and our "
              "records, so we only need the items below. ")
             + "This is the complete list, so you can send everything in one upload:", ""]
    lines += [f"{i}. {a}" for i, a in enumerate(asks, 1)]
    lines += ["", "Upload them through the client portal. If anything here is unclear, reply to this message and "
                  "we will call you.", "", "Client Onboarding team"]
    return "\n".join(lines)
