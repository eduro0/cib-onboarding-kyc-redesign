"""Every simulation input has a written reason, and the assumptions document shows each one with its model value.

Implements: kpi-model/assumptions-justified
"""

import re
import sys
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def inputs() -> dict:
    return {k: v for g in yaml.safe_load((ROOT / "model" / "assumptions.yaml").read_text()).values() for k, v in g.items()}


def test_assumptions_justified_every_input_has_a_reason():
    import build
    text = build.assumption_steps()
    for key in inputs():
        assert f"`{key}`" in text, f"{key} has no reason in the assumptions document"
    reasons = yaml.safe_load((ROOT / "model" / "assumption-reasons.yaml").read_text())
    known = build.sources()
    for group in reasons.values():
        for name, r in group.items():
            assert len(r["why"]) > 40, name
            assert not re.search(r"\b\d+(\.\d+)?\s*(h|hours|days|%)\b", r["why"]), f"{name}: restates a value; the build prints it"
            for k in r.get("src", []):
                assert k in known, (name, k)


def test_assumptions_justified_doc_shows_every_input_with_its_value():
    with zipfile.ZipFile(ROOT / "deliverables" / "docs" / "assumptions.docx") as z:
        xml = z.read("word/document.xml").decode()
    text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", xml))
    assert "simulated" in text and "[src:" not in text and "check:" not in text
    a = inputs()
    assert f"{a['asis.ubo.touch']['value']:g} h hands-on" in text
    assert f"{a['tobe.upload.wait']['value']:g} days elapsed" in text
    assert "onboarding 100%, review 60%" in text  # a per-case-type share shows both values
    for key in a:
        assert key in text, key
