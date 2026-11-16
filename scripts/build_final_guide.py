#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "FINAL_SUBMISSION_AND_DEFENSE_RU.md"
OUT = ROOT / "deliverables" / "Final_Submission_and_Defense_Guide_RU.docx"


def clean(text: str) -> str:
    return re.sub(r"\*\*(.*?)\*\*", r"\1", text).replace("`", "")


def shade(cell, color: str) -> None:
    props = cell._tc.get_or_add_tcPr()
    node = OxmlElement("w:shd")
    node.set(qn("w:fill"), color)
    props.append(node)


def add_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instr, end])


def add_table(doc: Document, lines: list[str]) -> None:
    rows = [[clean(cell.strip()) for cell in line.strip("|").split("|")] for line in lines]
    if len(rows) < 3:
        return
    headers = rows[0]
    data = [row for row in rows[2:] if len(row) == len(headers)]
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = True
    header_flag = OxmlElement("w:tblHeader")
    header_flag.set(qn("w:val"), "true")
    table.rows[0]._tr.get_or_add_trPr().append(header_flag)
    for cell, value in zip(table.rows[0].cells, headers):
        shade(cell, "17324D")
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(value)
        r.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        r.font.size = Pt(8.5)
    for index, values in enumerate(data):
        cells = table.add_row().cells
        for cell, value in zip(cells, values):
            if index % 2:
                shade(cell, "EDF3F7")
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cell.paragraphs[0].add_run(value).font.size = Pt(8.5)
    doc.add_paragraph()


def add_bullet(doc: Document, text: str, number: str | None = None) -> None:
    if number is None:
        p = doc.add_paragraph(style="List Bullet")
    else:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.first_line_indent = Inches(-0.18)
        p.add_run(f"{number}.  ")
    p.paragraph_format.space_after = Pt(3)
    p.add_run(clean(text))


def build() -> None:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)
    add_page_number(section.footer.paragraphs[0])

    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Arial")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial")
    normal.font.size = Pt(10)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    for name, size in (("Title", 22), ("Heading 1", 15), ("Heading 2", 12), ("Heading 3", 10.5)):
        style = doc.styles[name]
        style.font.name = "Arial"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Arial")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
    title_props = doc.styles["Title"]._element.get_or_add_pPr()
    title_border = title_props.find(qn("w:pBdr"))
    if title_border is not None:
        title_props.remove(title_border)

    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    in_code = False
    paragraph: list[str] = []

    def flush() -> None:
        if not paragraph:
            return
        p = doc.add_paragraph(clean(" ".join(paragraph)))
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(5)
        paragraph.clear()

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        if stripped.startswith("```"):
            flush()
            in_code = not in_code
            i += 1
            continue
        if in_code:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.space_after = Pt(1)
            r = p.add_run(stripped)
            r.font.name = "Menlo"
            r.font.size = Pt(8)
            i += 1
            continue
        if not stripped:
            flush()
            i += 1
            continue
        if stripped.startswith("|"):
            flush()
            table_lines: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            add_table(doc, table_lines)
            continue
        if stripped.startswith("# "):
            flush()
            p = doc.add_paragraph(style="Title")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run(clean(stripped[2:]))
            i += 1
            continue
        if stripped.startswith("## "):
            flush()
            doc.add_heading(clean(stripped[3:]), level=1)
            i += 1
            continue
        if stripped.startswith("### "):
            flush()
            doc.add_heading(clean(stripped[4:]), level=2)
            i += 1
            continue
        if stripped.startswith("- "):
            flush()
            add_bullet(doc, stripped[2:])
            i += 1
            continue
        numbered = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if numbered:
            flush()
            add_bullet(doc, numbered.group(2), number=numbered.group(1))
            i += 1
            continue
        paragraph.append(stripped)
        i += 1
    flush()

    core = doc.core_properties
    core.title = "Финальная сдача и защита: единая инструкция"
    core.subject = "Operational guide for the Kazakh LLM Error Study final submission"
    core.author = "Aldiyar Zhaksylyk; Yerkebulan Rakhymbay; Iliyas Aitzhan"
    core.comments = "Current as of 16 November 2026. Pre-results boundary is explicit."

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
