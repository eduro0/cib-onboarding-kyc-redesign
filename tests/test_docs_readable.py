"""The Word exports read well once converted to Google Docs: tables with borders, a shaded header, fitted columns.

Implements: package/readable-tables
"""

import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "deliverables" / "docs"


def test_exported_tables_have_borders_header_and_fitted_columns():
    seen = 0
    for docx in sorted(OUT.glob("*.docx")):
        with zipfile.ZipFile(docx) as z:
            xml = z.read("word/document.xml").decode()
        page = re.search(r'<w:pgSz w:w="(\d+)"', xml)
        margins = re.search(r'<w:pgMar [^>]*w:right="(\d+)"[^>]*w:left="(\d+)"', xml)
        assert page and margins, f"{docx.name}: no page size set"
        text_width = int(page.group(1)) - int(margins.group(1)) - int(margins.group(2))
        for table in re.findall(r"<w:tbl>.*?</w:tbl>", xml, re.S):
            seen += 1
            assert "<w:tblBorders>" in table, docx.name
            header = re.search(r"<w:tr>.*?</w:tr>", table, re.S).group(0)
            assert "<w:tblHeader" in header and "w:fill=" in header, f"{docx.name}: header row not shaded"
            widths = [int(w) for w in re.findall(r'<w:gridCol w:w="(\d+)"', table)]
            assert len(set(widths)) > 1, f"{docx.name}: every column the same width"
            assert abs(sum(widths) - text_width) <= len(widths), f"{docx.name}: table not the page's text width"
            assert text_width / len(widths) >= 1600, f"{docx.name}: {len(widths)} columns too narrow; use a wider page"
            assert '<w:sz w:val="18"' in table, f"{docx.name}: table text not set smaller than body text"
    assert seen >= 2
