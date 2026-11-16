#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from docx import Document
from docx.document import Document as DocumentObject
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

TABLE_CONTEXT = [
    (
        "Table 1 compares the closest studies and shows the methodological gap retained in this study.",
        "Table 1: Closest prior studies and retained evaluation gap",
    ),
    (
        "Table 2 records the four frozen model artifacts used by the local evaluation protocol.",
        "Table 2: Frozen local model artifacts",
    ),
    (
        "Table 3 maps each substantive responsibility to the evidence used during the defense.",
        "Table 3: Team ownership and defense evidence",
    ),
]


def iter_blocks(document: DocumentObject):
    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield Table(child, document)


def clear_body(document: DocumentObject) -> None:
    body = document.element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)


def add_text_paragraph(document: DocumentObject, source: Paragraph, style: str) -> Paragraph:
    target = document.add_paragraph(style=style)
    target.paragraph_format.keep_with_next = source.paragraph_format.keep_with_next
    if source.runs:
        for source_run in source.runs:
            target_run = target.add_run(source_run.text)
            target_run.bold = source_run.bold
            target_run.italic = source_run.italic
            target_run.underline = source_run.underline
            target_run.font.superscript = source_run.font.superscript
            target_run.font.subscript = source_run.font.subscript
    else:
        target.add_run(source.text)
    return target


def add_table(document: DocumentObject, source: Table) -> None:
    target = document.add_table(rows=len(source.rows), cols=len(source.columns))
    target.autofit = True
    for row_index, source_row in enumerate(source.rows):
        for column_index, source_cell in enumerate(source_row.cells):
            target_cell = target.cell(row_index, column_index)
            target_cell.text = ""
            paragraph = target_cell.paragraphs[0]
            paragraph.style = "TableCell"
            for source_paragraph_index, source_paragraph in enumerate(source_cell.paragraphs):
                if source_paragraph_index:
                    paragraph = target_cell.add_paragraph(style="TableCell")
                paragraph.add_run(source_paragraph.text)
            if row_index == 0:
                for run in paragraph.runs:
                    run.bold = True
    header_properties = target.rows[0]._tr.get_or_add_trPr()
    if header_properties.find(qn("w:tblHeader")) is None:
        header_properties.append(OxmlElement("w:tblHeader"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Transfer the controlled manuscript into the ACM Word template.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source = Document(args.source)
    output = Document(args.template)
    clear_body(output)
    output.core_properties.title = source.paragraphs[0].text
    output.core_properties.subject = "Controlled pre-results manuscript for ACM TALLIP"
    output.core_properties.author = "Aldiyar Zhaksylyk; Yerkebulan Rakhymbay; Iliyas Aitzhan"
    output.core_properties.last_modified_by = ""
    output.core_properties.revision = 1
    output.core_properties.keywords = "Kazakh; low-resource evaluation; error analysis; reproducibility"

    output.add_paragraph(source.paragraphs[0].text, style="Title_document")
    output.add_paragraph("Kazakh LLM Error Evaluation", style="Short Title")
    output.add_paragraph(source.paragraphs[1].text, style="Subtitle")
    for name in ("Aldiyar Zhaksylyk", "Yerkebulan Rakhymbay", "Iliyas Aitzhan"):
        output.add_paragraph(name, style="Authors")
    output.add_paragraph("SE-2417 · Kazakhstan · 2026", style="Affiliation")
    output.add_paragraph(source.paragraphs[4].text, style="Abstract")
    output.add_paragraph(source.paragraphs[5].text, style="CCSDescription")
    output.add_paragraph(source.paragraphs[6].text.replace("Keywords:", "Additional Keywords and Phrases:"), style="KeyWords")

    started = False
    reference_mode = False
    appendix_mode = False
    after_heading = False
    table_index = 0
    for block in iter_blocks(source):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if not started:
                started = block.style.name == "Heading 1" and text == "1 Introduction"
                if not started:
                    continue
            if not text:
                continue

            if block.style.name == "Heading 1":
                reference_mode = text == "References"
                appendix_mode = text.startswith("Appendix ")
                if reference_mode:
                    output.add_paragraph(text, style="ReferenceHead")
                elif appendix_mode:
                    output.add_paragraph(text, style="AppendixH1")
                else:
                    output.add_paragraph(text, style="Head1")
                after_heading = True
                continue
            if block.style.name == "Heading 2":
                output.add_paragraph(text, style="AppendixH2" if appendix_mode else "Head2")
                after_heading = True
                continue
            if reference_mode:
                add_text_paragraph(output, block, "Bib_entry")
                continue
            if block.style.name.startswith("List"):
                style = "List Paragraph"
            elif after_heading:
                style = "PostHeadPara"
            else:
                style = "Para"
            add_text_paragraph(output, block, style)
            after_heading = False
        else:
            if table_index >= len(TABLE_CONTEXT):
                raise ValueError("unexpected extra manuscript table")
            context, caption = TABLE_CONTEXT[table_index]
            output.add_paragraph(context, style="Para")
            output.add_paragraph(caption, style="TableCaption")
            add_table(output, block)
            table_index += 1

    if table_index != len(TABLE_CONTEXT):
        raise ValueError(f"expected {len(TABLE_CONTEXT)} tables, found {table_index}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.save(args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
