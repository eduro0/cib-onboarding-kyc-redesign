"""Tests for the access guide sent with the site.

Implements: package/access-guide
"""

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
sys.path.insert(0, str(ROOT / "scripts"))

# Every published item (the site's links plus the Drive folder), by the name a reader sees and the Google host it lives on.
PUBLISHED = {
    "Site": "sites.google.com/view/",
    "Deck": "docs.google.com/presentation/d/",
    "KPI model": "docs.google.com/spreadsheets/d/",
    "Dashboard": "datastudio.google.com/reporting/",
    "Assumptions": "docs.google.com/document/d/",
    "As-Is map": "drive.google.com/file/d/",
    "To-Be map": "drive.google.com/file/d/",
    "Roadmap": "docs.google.com/document/d/",
    "Change-risk register": "docs.google.com/document/d/",
    "Gemini Notebook": "notebook.google.com/notebook/",
    "Drive folder": "drive.google.com/drive/folders/",
}


def rows(text: str) -> dict[str, list[str]]:
    """The inventory table: first cell (bold name) to the other cells."""
    out = {}
    for line in text.splitlines():
        m = re.match(r"^\| \*\*(.+?)\*\* \|(.*)\|\s*$", line)
        if m:
            out[m.group(1)] = [c.strip() for c in m.group(2).split("|")]
    return out


def test_access_guide_lists_every_published_file_with_its_data_and_access():
    text = (DOCS / "access-guide.md").read_text()
    table = rows(text)
    for name, host in PUBLISHED.items():
        assert name in table, name
        link, holds, data, access = table[name]
        assert f"https://{host}" in link, name
        assert holds and data, name
        assert access.startswith(("Open", "Google sign-in")), (name, access)
    assert table["Gemini Notebook"][3].startswith("Google sign-in")
    assert "simulated" in text.lower() and "fictional" in text.lower()


def test_access_guide_exports_to_word():
    import build
    assert "access-guide" in build.PUBLIC_DOCS
    docx = ROOT / "deliverables" / "docs" / "access-guide.docx"
    with zipfile.ZipFile(docx) as z:
        xml = z.read("word/document.xml").decode()
        rels = z.read("word/_rels/document.xml.rels").decode()
    text = " ".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", xml))
    assert "[src:" not in text and "check:" not in text
    assert "<w:tbl>" in xml and rels.count("sites.google.com") >= 1, "table or links lost in the export"

