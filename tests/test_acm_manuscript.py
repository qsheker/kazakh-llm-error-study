from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "deliverables/Kazakh_LLM_Study_ACM_Submission.docx"


def test_acm_submission_copy_uses_template_styles_and_complete_content():
    document = Document(MANUSCRIPT)
    paragraph_text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    assert document.paragraphs[0].style.name == "Title_document"
    assert document.paragraphs[0].text == "Evaluating Kazakh Language Errors in Local Large Language Models"
    assert "Submission Template for ACM Papers" not in paragraph_text
    assert any(p.text == "Results" and p.style.name == "Head1" for p in document.paragraphs)
    assert "Results reporting contract" not in paragraph_text
    assert "controlled pre-results" not in paragraph_text.lower()
    assert "KazLLM had the lowest" in paragraph_text
    assert sum(p.style.name == "Bib_entry" for p in document.paragraphs) == 28
    assert sum(p.style.name == "TableCaption" for p in document.paragraphs) == 6
    assert len(document.tables) == 6


def test_acm_submission_core_word_count_meets_course_range():
    document = Document(MANUSCRIPT)
    words = []
    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            paragraph = Paragraph(child, document)
            if paragraph.text.strip() == "References":
                break
            words.extend(paragraph.text.split())
        elif child.tag == qn("w:tbl"):
            table = Table(child, document)
            for row in table.rows:
                for cell in row.cells:
                    words.extend(cell.text.split())
    assert 4500 <= len(words) <= 7500
