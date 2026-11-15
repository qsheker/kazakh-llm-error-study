#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables" / "Cover_Letter_TALLIP.docx"


def paragraph(doc: Document, text: str, *, space_after: int = 7) -> None:
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.05


def main() -> None:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.9)
    section.right_margin = Inches(0.9)

    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Arial")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial")
    normal.font.size = Pt(10.5)

    warning = doc.add_paragraph()
    warning.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = warning.add_run("DRAFT — DO NOT SUBMIT UNTIL THE FINAL EVIDENCE GATE PASSES")
    run.bold = True
    run.font.color.rgb = RGBColor(178, 34, 34)
    run.font.size = Pt(10)

    p = doc.add_paragraph("15 November 2026")
    p.paragraph_format.space_after = Pt(8)
    p = doc.add_paragraph("Editors\nACM Transactions on Asian and Low-Resource Language Information Processing")
    p.paragraph_format.space_after = Pt(10)

    paragraph(doc, "Dear Editors,")
    paragraph(
        doc,
        "Please consider the manuscript \"Evaluating Kazakh Language Errors in Local Large Language Models\" as a research article for ACM Transactions on Asian and Low-Resource Language Information Processing. The frozen study design specifies a controlled local comparison of four quantized language-model artifacts on 60 Kazakh educational and public-information prompts, for a planned total of 240 paired responses under one generation protocol.",
    )
    paragraph(
        doc,
        "The contribution is not a general model leaderboard. It is a reproducible error-analysis design that combines immutable model and request provenance, a balanced Kazakh prompt resource, two independent blinded span-level annotations, adjudication before unblinding, and paired nonparametric inference with whole-prompt uncertainty estimates. The primary outcome is the number of adjudicated grammatical, lexical, semantic and code-switching events per 100 word tokens.",
    )
    paragraph(
        doc,
        "The manuscript fits TALLIP because it addresses practical language processing for an Asian low-resource language and releases reusable evaluation materials. It is directly aligned with recent TALLIP work on Vietnamese task-specific language models, Tibetan large language models and fine-grained Chinese evaluation benchmarks, while adding a different evidence layer: controlled local inference and human linguistic error events rather than training performance or task accuracy alone.",
    )
    paragraph(
        doc,
        "The accompanying repository records the exact Ollama content digests, templates, runtime controls, environment, prompt and reference-card freeze, raw request receipts, annotation workflow and generated statistics. Model binaries are not redistributed. The study does not intentionally collect personal data or external human-participant data; the annotators are the authors. Generative-AI assistance in software and manuscript preparation is disclosed, and no AI-generated label is represented as an independent human annotation.",
    )
    paragraph(
        doc,
        "All authors must approve the frozen manuscript and release before this letter is used. At submission, we will confirm that the manuscript is original, not under review elsewhere, that all references have been personally verified, and that every reported number is traceable to the released logs and generated tables.",
    )
    paragraph(doc, "Thank you for your consideration.")

    p = doc.add_paragraph("Sincerely,\nAldiyar Zhaksylyk\nYerkebulan Rakhymbay\nIliyas Aitzhan")
    p.paragraph_format.space_before = Pt(4)

    core = doc.core_properties
    core.title = "Draft cover letter to ACM TALLIP"
    core.author = "Aldiyar Zhaksylyk; Yerkebulan Rakhymbay; Iliyas Aitzhan"
    core.comments = "Draft only. Do not submit until human annotations, results, checks, and author approvals are frozen."

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
