"""
pdf_builder.py
--------------
Generates a one-page resume laid out like the sample:
centered name, icon contact row, underlined sections, and a bottom bar.
"""

import os
import re

from fpdf import FPDF

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

PHONE_ICON = "\uE717"
MAIL_ICON = "\uE715"
PIN_ICON = "\uE7B7"


def clean_text(text, unicode_font=True):
    """Normalize punctuation. Core fonts cannot draw characters outside Latin-1."""
    if not text:
        return ""
    replacements = {
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        "\u2011": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    if not unicode_font:
        return text.encode("latin-1", "ignore").decode("latin-1")
    return text


def split_items(text):
    """Turn a comma list or one-item-per-line block into clean labels."""
    text = (text or "").strip()
    if not text:
        return []
    if "\n" in text:
        parts = text.splitlines()
    else:
        parts = text.split(",")
    return [part.strip("•- \t") for part in parts if part.strip("•- \t")]


def parse_languages(text):
    """Read 'English | Native' lines, or 'English (Native)' items."""
    languages = []
    for item in split_items(text):
        if "|" in item:
            name, level = item.split("|", 1)
        elif " - " in item:
            name, level = item.split(" - ", 1)
        elif "(" in item and item.endswith(")"):
            name, level = item[:-1].split("(", 1)
        else:
            name, level = item, ""
        name, level = name.strip(), level.strip()
        if name:
            languages.append((name, level))
    return languages


def parse_entries(text):
    """
    Split a block of text into resume entries.

    A blank line starts a new entry. Inside an entry the first line is
    "Organization | dates", the second line is the bold role, and the rest
    is the description.
    """
    text = (text or "").strip()
    if not text:
        return []

    entries = []
    for block in re.split(r"\n\s*\n", text):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if len(lines) == 1:
            meta, title, body = "", lines[0], []
        else:
            meta, title, body = lines[0], lines[1], lines[2:]
        entries.append({"meta": meta, "title": title, "body": body})
    return entries


class ResumePDF(FPDF):
    def header(self):
        pass

    def footer(self):
        # Charcoal bar sitting on the bottom edge of the page.
        self.set_fill_color(78, 78, 78)
        self.rect(0, self.h - 14, self.w, 14, style="F")


def _load_fonts(pdf):
    """Use Arial when Windows provides it. Fall back to the built-in Helvetica."""
    regular = r"C:\Windows\Fonts\arial.ttf"
    bold = r"C:\Windows\Fonts\arialbd.ttf"
    icons = r"C:\Windows\Fonts\segmdl2.ttf"
    unicode_font = os.path.exists(regular) and os.path.exists(bold)
    if unicode_font:
        pdf.add_font("Resume", "", regular)
        pdf.add_font("Resume", "B", bold)
        family = "Resume"
    else:
        family = "Helvetica"
    icons_ok = os.path.exists(icons)
    if icons_ok:
        pdf.add_font("Icons", "", icons)
    return family, unicode_font, icons_ok


def _section_title(pdf, font, title):
    pdf.ln(3)
    pdf.set_font(font, "B", 11.5)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, title.upper(), new_x="LMARGIN", new_y="NEXT")
    y = pdf.get_y() + 0.6
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.4)
    pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
    pdf.set_y(y + 3.2)


def _paragraph(pdf, font, text, unicode_font):
    pdf.set_font(font, "", 10)
    pdf.set_text_color(35, 35, 35)
    pdf.multi_cell(
        0,
        5.0,
        clean_text(text, unicode_font),
        align="J",
        new_x="LMARGIN",
        new_y="NEXT",
    )


def _write_entry(pdf, font, entry, unicode_font):
    if entry["meta"]:
        pdf.set_font(font, "", 10)
        pdf.set_text_color(25, 25, 25)
        pdf.cell(
            0, 5, clean_text(entry["meta"], unicode_font), new_x="LMARGIN", new_y="NEXT"
        )
    if entry["title"]:
        pdf.set_font(font, "B", 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(
            0,
            5.4,
            clean_text(entry["title"], unicode_font),
            new_x="LMARGIN",
            new_y="NEXT",
        )
    body = entry["body"]
    if body:
        pdf.ln(0.6)
        bullet_lines = all(line.lstrip().startswith(("-", "•")) for line in body)
        if bullet_lines:
            for line in body:
                item = line.lstrip("-• ").strip()
                _paragraph(pdf, font, f"-  {item}", unicode_font)
        else:
            _paragraph(pdf, font, " ".join(body), unicode_font)
    pdf.ln(3.2)


def _contact_row(pdf, font, unicode_font, icons_ok, phone, email, location):
    items = []
    if phone:
        items.append((PHONE_ICON, phone))
    if email:
        items.append((MAIL_ICON, email))
    if location:
        items.append((PIN_ICON, location))
    if not items:
        return

    pdf.set_font(font, "", 9.5)
    icon_slot = 4.6 if icons_ok else 0
    gap = 8
    widths = []
    labels = []
    for _, text in items:
        label = clean_text(text, unicode_font)
        labels.append(label)
        widths.append(icon_slot + pdf.get_string_width(label))

    total = sum(widths) + gap * (len(items) - 1)
    x = (pdf.w - total) / 2
    y = pdf.get_y()
    pdf.set_text_color(30, 30, 30)

    for (icon, _), label, width in zip(items, labels, widths):
        if icons_ok:
            pdf.set_font("Icons", "", 8.5)
            pdf.set_xy(x, y + 0.3)
            pdf.cell(4.2, 4.5, icon)
        pdf.set_font(font, "", 9.5)
        pdf.set_xy(x + icon_slot, y)
        pdf.cell(width - icon_slot + 0.4, 5, label)
        x += width + gap

    pdf.set_xy(pdf.l_margin, y + 8)


def _skills(pdf, font, unicode_font, skills):
    pdf.set_font(font, "", 10)
    pdf.set_text_color(30, 30, 30)
    col_w = pdf.epw / 3
    row_h = 6
    for index, skill in enumerate(skills):
        column = index % 3
        if column == 0 and index:
            pdf.ln(row_h)
        x = pdf.l_margin + column * col_w
        y = pdf.get_y()
        pdf.set_xy(x, y)
        pdf.cell(col_w - 2, row_h, clean_text(f"•   {skill}", unicode_font))
    pdf.ln(row_h)


def build_resume_pdf(template_name: str, data: dict) -> str:
    """Builds the PDF and returns the path."""
    os.makedirs(DATA_DIR, exist_ok=True)

    safe_name = clean_text(data.get("name", "Resume"), unicode_font=False)
    safe_name = safe_name.replace(" ", "_").replace("/", "_") or "Resume"
    output_path = os.path.join(DATA_DIR, f"{safe_name}_Resume.pdf")

    pdf = ResumePDF()
    font, unicode_font, icons_ok = _load_fonts(pdf)
    pdf.set_margins(16, 14, 16)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    pdf.set_font(font, "B", 22)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(
        0,
        11,
        clean_text(data.get("name", "Name"), unicode_font).upper(),
        align="C",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.set_font(font, "", 12)
    pdf.cell(
        0,
        7,
        clean_text(data.get("title", ""), unicode_font),
        align="C",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(2.5)

    _contact_row(
        pdf,
        font,
        unicode_font,
        icons_ok,
        data.get("phone", ""),
        data.get("email", ""),
        data.get("location", ""),
    )

    summary = (data.get("summary") or "").strip()
    if summary:
        _section_title(pdf, font, "About Me")
        _paragraph(pdf, font, summary, unicode_font)

    for heading, key in (
        ("Education", "education"),
        ("Work Experience", "experience"),
    ):
        entries = parse_entries(data.get(key, ""))
        if not entries:
            continue
        _section_title(pdf, font, heading)
        for entry in entries:
            _write_entry(pdf, font, entry, unicode_font)

    skills = split_items(data.get("skills"))
    if skills:
        _section_title(pdf, font, "Skills")
        _skills(pdf, font, unicode_font, skills)

    communication = split_items(data.get("communication"))
    if communication:
        _section_title(pdf, font, "Communication")
        _skills(pdf, font, unicode_font, communication)

    certificates = parse_entries(data.get("certificates"))
    if certificates:
        _section_title(pdf, font, "Certificates")
        for entry in certificates:
            _write_entry(pdf, font, entry, unicode_font)

    languages = parse_languages(data.get("languages"))
    if languages:
        _section_title(pdf, font, "Languages")
        labels = [f"{name} - {level}" if level else name for name, level in languages]
        _skills(pdf, font, unicode_font, labels)

    pdf.output(output_path)
    return output_path
