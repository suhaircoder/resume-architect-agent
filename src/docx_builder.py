"""
docx_builder.py
---------------
Writes the same resume as an editable Word file employers can open directly.
"""

import os

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from src.pdf_builder import DATA_DIR, parse_entries, parse_languages, split_items

DARK = RGBColor(0x1A, 0x1A, 0x1A)


def _set_run(run, text, size, bold=False, color=DARK):
    run.text = text
    run.bold = bold
    run.font.name = "Arial"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    run.font.size = Pt(size)
    run.font.color.rgb = color


def _paragraph(doc, text, size=10, bold=False, align="left", space_before=0, space_after=2):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(space_before)
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.paragraph_format.line_spacing = 1.08
    if align == "center":
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "justify":
        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    _set_run(paragraph.add_run(), text, size, bold=bold)
    return paragraph


def _section_heading(doc, title):
    paragraph = _paragraph(doc, title.upper(), size=12, bold=True, space_before=12, space_after=4)
    p_pr = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "12")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "000000")
    borders.append(bottom)
    p_pr.append(borders)
    return paragraph


def _hide_table_borders(table):
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "nil")
        borders.append(element)
    tbl_pr.append(borders)


def _bullet_grid(doc, items):
    columns = 3
    rows = (len(items) + columns - 1) // columns
    table = doc.add_table(rows=rows, cols=columns)
    table.autofit = True
    _hide_table_borders(table)
    for index, item in enumerate(items):
        cell = table.rows[index // columns].cells[index % columns]
        cell.text = ""
        paragraph = cell.paragraphs[0]
        paragraph.paragraph_format.space_after = Pt(2)
        _set_run(paragraph.add_run(), f"•  {item}", 10)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def _write_entries(doc, entries):
    for entry in entries:
        if entry["meta"]:
            _paragraph(doc, entry["meta"], size=10, space_before=4, space_after=0)
        if entry["title"]:
            _paragraph(doc, entry["title"], size=11, bold=True, space_before=0, space_after=1)
        body = entry["body"]
        if not body:
            continue
        bullet_lines = all(line.lstrip().startswith(("-", "•")) for line in body)
        if bullet_lines:
            for line in body:
                _paragraph(doc, f"•  {line.lstrip('-• ').strip()}", size=10, space_after=1)
        else:
            _paragraph(doc, " ".join(body), size=10, align="justify", space_after=4)


def build_resume_docx(data: dict) -> str:
    """Builds the Word resume and returns the path."""
    os.makedirs(DATA_DIR, exist_ok=True)
    safe_name = (data.get("name") or "Resume").replace(" ", "_").replace("/", "_")
    output_path = os.path.join(DATA_DIR, f"{safe_name}_Resume.docx")

    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(1.5)
        section.bottom_margin = Cm(1.5)
        section.left_margin = Cm(1.6)
        section.right_margin = Cm(1.6)
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)

    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(10)

    _paragraph(doc, (data.get("name") or "Name").upper(), size=22, bold=True, align="center", space_after=0)
    if data.get("title"):
        _paragraph(doc, data["title"], size=12, align="center", space_before=2, space_after=2)

    contact = "   |   ".join(
        part for part in (data.get("phone"), data.get("email"), data.get("location")) if part
    )
    if contact:
        _paragraph(doc, contact, size=10, align="center", space_before=2, space_after=4)

    summary = (data.get("summary") or "").strip()
    if summary:
        _section_heading(doc, "About Me")
        _paragraph(doc, summary, align="justify", space_after=4)

    education = parse_entries(data.get("education"))
    if education:
        _section_heading(doc, "Education")
        _write_entries(doc, education)

    experience = parse_entries(data.get("experience"))
    if experience:
        _section_heading(doc, "Work Experience")
        _write_entries(doc, experience)

    skills = split_items(data.get("skills"))
    if skills:
        _section_heading(doc, "Skills")
        _bullet_grid(doc, skills)

    communication = split_items(data.get("communication"))
    if communication:
        _section_heading(doc, "Communication")
        _bullet_grid(doc, communication)

    certificates = parse_entries(data.get("certificates"))
    if certificates:
        _section_heading(doc, "Certificates")
        _write_entries(doc, certificates)

    languages = parse_languages(data.get("languages"))
    if languages:
        _section_heading(doc, "Languages")
        labels = [f"{name} - {level}" if level else name for name, level in languages]
        _bullet_grid(doc, labels)

    doc.save(output_path)
    return output_path
