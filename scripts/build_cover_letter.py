#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables" / "Cover_Letter_TALLIP.docx"


def paragraph(doc: Document, text: str, *, space_after: int = 6) -> None:
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.0


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
    normal.font.size = Pt(10)

    p = doc.add_paragraph()
    p.add_run("16 November 2026")
    p.add_run().add_break()
    p.add_run("Editors")
    p.add_run().add_break()
    p.add_run("ACM Transactions on Asian and Low-Resource Language Information Processing")
    p.paragraph_format.space_after = Pt(8)

    paragraph(doc, "Dear Editors,")
    paragraph(
        doc,
        "Please consider the manuscript \"Evaluating Kazakh Language Errors in Local Large Language Models\" as a research article for ACM Transactions on Asian and Low-Resource Language Information Processing. The study compares four quantized language-model artifacts on 60 Kazakh educational and public-information prompts. The executed run retains all 240 request receipts under one frozen generation protocol and links every reported result to a reviewed, source-bound team gold set.",
    )
    paragraph(
        doc,
        "The contribution is not a general model leaderboard. It is a reproducible error-analysis design that combines immutable model and request provenance, a balanced Kazakh prompt resource, disclosed joint-team AI-assisted span review before unblinding, and paired nonparametric inference with whole-prompt uncertainty estimates. The primary outcome is the number of reviewed grammatical, lexical, semantic and code-switching events per 100 word tokens. The workflow produces one team-consensus gold set and does not claim independent-rater reliability.",
    )
    paragraph(
        doc,
        "The manuscript fits TALLIP because it addresses practical language processing for an Asian low-resource language and releases reusable evaluation materials. It is directly aligned with recent TALLIP work on Vietnamese task-specific language models, Tibetan large language models and fine-grained Chinese evaluation benchmarks, while adding a different evidence layer: controlled local inference and human linguistic error events rather than training performance or task accuracy alone.",
    )
    paragraph(
        doc,
        "The accompanying repository records the exact Ollama content digests, templates, runtime controls, environment, prompt and reference-card freeze, raw request receipts, annotation workflow and generated statistics. Model binaries are not redistributed. The study does not intentionally collect personal data or external human-participant data; the reviewers are the authors. Generative-AI assistance in software, manuscript preparation and draft annotation is disclosed, and the resulting team gold is not represented as independent human annotation.",
    )
    paragraph(
        doc,
        "The models differed across paired prompts, and KazLLM had the lowest mean reviewed primary-error rate. Its pre-specified contrast with Llama was 2.53 fewer events per 100 words, with a 95% whole-prompt bootstrap interval from 1.14 to 3.94 and Holm-adjusted p = 0.01134. Semantic errors were the most frequent category among the three general-purpose models. Code-switching was rare, and the hybrid detector's apparent F1 improvement remained uncertain because its bootstrap interval included zero.",
    )
    paragraph(doc, "Thank you for your consideration.")

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(0)
    for index, line in enumerate(
        ("Sincerely,", "Aldiyar Zhaksylyk", "Yerkebulan Rakhymbay", "Iliyas Aitzhan")
    ):
        if index:
            p.add_run().add_break()
        p.add_run(line)

    core = doc.core_properties
    core.title = "Cover letter to ACM TALLIP"
    core.author = "Aldiyar Zhaksylyk; Yerkebulan Rakhymbay; Iliyas Aitzhan"
    core.comments = "Prepared from the frozen final analysis; external submission still requires the journal's ordinary author and policy checks."

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
