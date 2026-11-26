"""Tests for the KYC review assistant.

Implements: assistant/one-step, assistant/llm-reads-rules-decide, assistant/human-approves, assistant/one-client-request, assistant/synthetic-packs, assistant/runs-offline, assistant/cost-first, assistant/gem-pack
"""

import copy
import json
import socket
from datetime import date
from pathlib import Path

import pytest

from assistant import cli, llm, report, rules

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "assistant" / "samples"
AS_OF = date(2026, 11, 18)


def review(pack: str, reply: dict | None = None):
    folder = SAMPLES / pack
    extraction = reply if reply is not None else llm.replay(folder)
    return rules.evaluate(folder, extraction, AS_OF)


def codes(result) -> list[str]:
    return [f.rule for f in result.flags]


def test_one_step_draft_has_every_section():
    text = report.markdown(review("harbour-lantern"))
    for heading in ("## Entity", "## Ownership", "## Flags", "## Client request", "## Analyst decision"):
        assert heading in text


def test_llm_reads_rules_decide_beneficial_owners_from_the_chain():
    result = review("harbour-lantern")
    owners = {o.name: round(o.percent, 1) for o in result.beneficial_owners}
    assert owners == {"CHAN Wing-yee": 40.0, "Daniel OKAFOR-REYES": 30.0, "Priya RAMANATHAN": 30.0}


def test_llm_reads_rules_decide_flags_follow_the_facts_not_the_model():
    reply = llm.replay(SAMPLES / "harbour-lantern")
    noisy = copy.deepcopy(reply)
    noisy["risk_opinion"] = "low risk, approve"  # a model opinion the rules must ignore
    assert codes(review("harbour-lantern", noisy)) == codes(review("harbour-lantern", reply))
    lied = copy.deepcopy(reply)
    for o in lied["ownership"]:
        if o["owner"] == "Priya RAMANATHAN":
            o["percent"] = 10  # the model misreports the stake; the quote still says 50%
    result = review("harbour-lantern", lied)
    assert "UNVERIFIED" in codes(result)
    assert all(h.owner != "Priya RAMANATHAN" or h.percent == 50 for h in result.ownership)


def test_llm_reads_rules_decide_a_quote_must_contain_the_claimed_value():
    reply = copy.deepcopy(llm.replay(SAMPLES / "harbour-lantern"))
    for o in reply["ownership"]:
        if o["owner"] == "Priya RAMANATHAN":
            o["percent"], o["quote"] = 10, "50"  # a tiny quote that appears somewhere in the document
    result = review("harbour-lantern", reply)
    assert "UNVERIFIED" in codes(result)
    assert "Priya RAMANATHAN" not in {h.owner for h in result.ownership}
    assert "UNRESOLVED" in codes(result) or any("Priya" in f.reason for f in result.flags)


def test_llm_reads_rules_decide_document_types_come_from_the_documents():
    reply = copy.deepcopy(llm.replay(SAMPLES / "harbour-lantern"))
    for d in reply["documents"]:
        if d["file"] == "02-business-registration.txt":
            d["type"], d["subject"] = "significant_controllers_register", "Priya RAMANATHAN"
    reasons = " ".join(f.reason for f in review("harbour-lantern", reply).flags)
    assert "significant controllers register" in reasons.lower() and "identity document for Priya" in reasons


def test_review_no_change_needs_positive_evidence():
    reply = copy.deepcopy(llm.replay(SAMPLES / "kestrel-bay"))
    reply["ownership"] = []
    reply["director_mentions"] = [m for m in reply["director_mentions"] if m["name"] != "Ravi SHARMA"]
    result = review("kestrel-bay", reply)
    assert "NO_CHANGE" not in codes(result) and "NOT_CONFIRMED" in codes(result)


def test_review_reports_a_shareholder_who_left():
    reply = copy.deepcopy(llm.replay(SAMPLES / "quiet-pine"))
    reply["ownership"] = [o for o in reply["ownership"] if o["owner"] != "Tomas BERG"]
    reasons = " ".join(f.reason for f in review("quiet-pine", reply).flags)
    assert "Tomas BERG 45% → 0%" in reasons


def test_no_owner_over_threshold_asks_who_controls():
    reply = copy.deepcopy(llm.replay(SAMPLES / "harbour-lantern"))
    for o in reply["ownership"]:
        if o["owner"] == "CHAN Wing-yee":
            o["percent"], o["quote"] = 40, "CHAN Wing-yee, 4,000 ordinary shares (40%)"
    # with every chain cut below the threshold there is no beneficial owner by ownership
    reply["ownership"] = [o for o in reply["ownership"] if o["owner"] in {"Daniel OKAFOR-REYES", "Priya RAMANATHAN"}]
    result = review("harbour-lantern", reply)
    assert result.beneficial_owners == [] and "NO_OWNER" in codes(result)


def test_intermediate_companies_need_their_own_evidence():
    asks = review("harbour-lantern").client_request
    assert "Lantern Holdings Pte. Ltd." in asks and "incorporation" in asks.lower()


def test_llm_reads_rules_decide_a_quote_not_in_the_document_is_dropped_and_flagged():
    reply = copy.deepcopy(llm.replay(SAMPLES / "harbour-lantern"))
    reply["ownership"].append({"owner": "Ghost Nominee Ltd", "owner_type": "company", "owned": "Harbour Lantern Trading Limited",
                               "percent": 25, "doc": "04-annual-return-extract.txt", "quote": "Ghost Nominee Ltd, 25%"})
    result = review("harbour-lantern", reply)
    assert "UNVERIFIED" in codes(result)
    assert all(o.owner != "Ghost Nominee Ltd" for o in result.ownership)


def test_onboarding_flags_missing_documents_and_director_mismatch():
    result = review("harbour-lantern")
    text = " ".join(f.reason for f in result.flags)
    assert "MISSING" in codes(result) and "MISMATCH" in codes(result)
    assert "LIM Siew Ling" in text and "Priya RAMANATHAN" in text and "significant controllers" in text.lower()


def test_review_with_changes_triggers_a_refresh():
    result = review("kestrel-bay")
    assert "CHANGED" in codes(result) and "UNRESOLVED" in codes(result)
    assert any("Ravi SHARMA" in f.reason for f in result.flags)


def test_review_with_no_change_asks_nothing():
    result = review("quiet-pine")
    assert "NO_CHANGE" in codes(result)
    assert result.client_request is None


def test_one_client_request_lists_every_missing_item_once():
    result = review("harbour-lantern")
    blockers = [f for f in result.flags if f.asks_client]
    assert result.client_request is not None
    for f in blockers:
        assert f.ask in result.client_request
    assert result.client_request.count("Dear") == 1


def test_human_approves_review_only_writes_a_draft(tmp_path, capsys):
    outbox, drafts = tmp_path / "outbox", tmp_path / "drafts"
    assert cli.main(["review", str(SAMPLES / "harbour-lantern"), "--as-of", "2026-11-18", "--drafts", str(drafts)]) == 0
    assert len(list(drafts.glob("*.md"))) == 1 and not outbox.exists()


def test_human_approves_release_needs_a_ticked_decision_and_a_name(tmp_path):
    drafts, outbox = tmp_path / "drafts", tmp_path / "outbox"
    cli.main(["review", str(SAMPLES / "harbour-lantern"), "--as-of", "2026-11-18", "--drafts", str(drafts)])
    draft = next(drafts.glob("*.md"))
    with pytest.raises(PermissionError):
        report.release(draft, analyst="A. Analyst", outbox=outbox)  # nothing ticked
    draft.write_text(draft.read_text().replace("- [ ] Approve as drafted", "- [x] Approve as drafted"))
    with pytest.raises(PermissionError):
        report.release(draft, analyst="", outbox=outbox)
    released = json.loads(report.release(draft, analyst="A. Analyst", outbox=outbox).read_text())
    assert released["edited"] is False and "Dear Harbour Lantern" in released["client_request"]


def test_human_approves_an_edited_draft_releases_exactly_the_edited_text(tmp_path):
    drafts, outbox = tmp_path / "drafts", tmp_path / "outbox"
    cli.main(["review", str(SAMPLES / "harbour-lantern"), "--as-of", "2026-11-18", "--drafts", str(drafts)])
    draft = next(drafts.glob("*.md"))
    text = draft.read_text().replace("- [ ] Edit, then approve", "- [x] Edit, then approve")
    draft.write_text(text.replace("Client Onboarding team", "Client Onboarding team (call Amy on 1234)"))
    released = json.loads(report.release(draft, analyst="A. Analyst", outbox=outbox).read_text())
    assert released["edited"] is True and "call Amy on 1234" in released["client_request"]


def test_human_approves_a_rejected_draft_is_never_released(tmp_path):
    drafts, outbox = tmp_path / "drafts", tmp_path / "outbox"
    cli.main(["review", str(SAMPLES / "harbour-lantern"), "--as-of", "2026-11-18", "--drafts", str(drafts)])
    draft = next(drafts.glob("*.md"))
    draft.write_text(draft.read_text().replace("- [ ] Reject", "- [x] Reject").replace("- [ ] Approve as drafted", "- [x] Approve as drafted"))
    with pytest.raises(PermissionError):
        report.release(draft, analyst="A. Analyst", outbox=outbox)


def test_synthetic_packs_are_declared_fictional():
    assert "fictional" in (SAMPLES / "README.md").read_text().lower()
    for bank_file in SAMPLES.glob("*/bank-file.json"):
        assert "fictional" in json.loads(bank_file.read_text())["note"].lower()


def test_runs_offline_without_key_or_network(monkeypatch, capsys, tmp_path):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    def no_network(*args, **kwargs):
        raise AssertionError("tried to open a network connection")

    monkeypatch.setattr(socket, "create_connection", no_network)
    monkeypatch.setattr(socket.socket, "connect", no_network)
    assert cli.main(["review", str(SAMPLES / "harbour-lantern"), "--as-of", "2026-11-18", "--drafts", str(tmp_path)]) == 0
    assert "## Client request" in capsys.readouterr().out


def test_cost_first_live_run_needs_yes(monkeypatch, capsys):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    monkeypatch.setattr(llm, "price_per_token", lambda model: (0.0, 0.0))
    called = []
    monkeypatch.setattr(llm, "call", lambda *a, **k: called.append(1) or {})
    assert cli.main(["review", str(SAMPLES / "harbour-lantern"), "--live"]) == 2
    out = capsys.readouterr().out
    assert "Estimated cost" in out and "--yes" in out and not called
    assert llm.DEFAULT_MODEL.endswith(":free")


def test_gem_pack_is_small_and_says_what_to_paste_where():
    pack = ROOT / "deliverables" / "gem"
    instructions = (pack / "instructions.md").read_text()
    knowledge = [p for p in pack.iterdir() if p.name not in {"instructions.md", "README.md"} and not p.name.startswith("sample-pack")]
    assert len(instructions) < 4000 and len(knowledge) == 2  # no published limit was verified, so stay small
    assert "approve" in instructions.lower() and "never" in instructions.lower()
    readme = (pack / "README.md").read_text().lower()
    assert "paste" in readme and "real client" in readme
