#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "deliverables" / "team_handoff"
CALIBRATION_DIR = ROOT / "annotations" / "calibration" / "dev_calibration_v2"


RATERS = {
    "rater_1": {
        "name": "Yerkebulan Rakhymbay",
        "short_name": "Yerkebulan",
        "role": "Rater 1",
        "future": (
            "После калибровки ты независимо размечаешь полный Rater 1 workbook на 240 ответов, "
            "проверяешь тесты, статистические таблицы и интерпретацию H1-H4. На защите ты "
            "объясняешь primary endpoint, agreement, permutation Friedman test, Kendall's W, "
            "Pratt pairwise tests, Holm correction и bootstrap intervals."
        ),
    },
    "rater_2": {
        "name": "Iliyas Aitzhan",
        "short_name": "Iliyas",
        "role": "Rater 2",
        "future": (
            "После калибровки ты независимо размечаешь полный Rater 2 workbook на 240 ответов. "
            "После разморозки результатов ты переносишь только сгенерированные таблицы и графики "
            "в manuscript и slides, затем проверяешь совпадение каждого числа, journal fit, "
            "declarations, references и соответствие ACM template."
        ),
    },
}


def set_repeat_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    marker = OxmlElement("w:tblHeader")
    marker.set(qn("w:val"), "true")
    tr_pr.append(marker)


def set_cell_fill(cell, color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shading = tc_pr.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        tc_pr.append(shading)
    shading.set(qn("w:fill"), color)


def set_cell_margins(cell, top=100, start=120, bottom=100, end=120) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_borders(table, color: str = "D9D9D9") -> None:
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        node = borders.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            borders.append(node)
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), "4")
        node.set(qn("w:space"), "0")
        node.set(qn("w:color"), color)


def set_keep_with_next(paragraph) -> None:
    paragraph.paragraph_format.keep_with_next = True


def remove_paragraph_borders(element) -> None:
    paragraph_properties = element.get_or_add_pPr()
    borders = paragraph_properties.find(qn("w:pBdr"))
    if borders is not None:
        paragraph_properties.remove(borders)


def add_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run("Страница ")
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instruction, end])


def add_table(doc: Document, headers: list[str], rows: list[list[str]], widths: list[float]) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.autofit = False
    set_table_borders(table)
    set_repeat_header(table.rows[0])
    for idx, (cell, header) in enumerate(zip(table.rows[0].cells, headers)):
        cell.width = Inches(widths[idx])
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_fill(cell, "17324D")
        set_cell_margins(cell)
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run(header)
        run.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        run.font.size = Pt(9.5)
    for row_index, values in enumerate(rows):
        cells = table.add_row().cells
        for idx, (cell, value) in enumerate(zip(cells, values)):
            cell.width = Inches(widths[idx])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)
            if row_index % 2:
                set_cell_fill(cell, "EDF3F7")
            paragraph = cell.paragraphs[0]
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            paragraph.paragraph_format.space_after = Pt(0)
            run = paragraph.add_run(value)
            run.font.size = Pt(9.5)
    doc.add_paragraph()


def add_bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        paragraph = doc.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.space_after = Pt(3)
        paragraph.add_run(item)


def add_numbered(doc: Document, items: list[str]) -> None:
    for item in items:
        paragraph = doc.add_paragraph(style="List Number")
        paragraph.paragraph_format.space_after = Pt(4)
        paragraph.add_run(item)


def add_code(doc: Document, command: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.left_indent = Inches(0.25)
    paragraph.paragraph_format.right_indent = Inches(0.25)
    paragraph.paragraph_format.space_before = Pt(2)
    paragraph.paragraph_format.space_after = Pt(6)
    run = paragraph.add_run(command)
    run.font.name = "Courier New"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Courier New")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Courier New")
    run.font.size = Pt(9)


def configure_document(doc: Document, owner: str, role: str) -> None:
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)
    section.footer_distance = Inches(0.3)

    footer = section.footer.paragraphs[0]
    footer.add_run(f"{owner}  {role}     ")
    add_page_number(footer)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Arial"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Arial")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial")
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.08
    for style_name, size in (("Title", 22), ("Heading 1", 15), ("Heading 2", 12)):
        style = styles[style_name]
        style.font.name = "Arial"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Arial")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial")
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.bold = True
        remove_paragraph_borders(style._element)
    styles["Heading 1"].paragraph_format.space_before = Pt(10)
    styles["Heading 1"].paragraph_format.space_after = Pt(5)
    styles["Heading 1"].paragraph_format.keep_with_next = True
    styles["Heading 2"].paragraph_format.space_before = Pt(7)
    styles["Heading 2"].paragraph_format.space_after = Pt(3)
    styles["Heading 2"].paragraph_format.keep_with_next = True


def file_record(manifest: dict, phase: str, rater: str) -> dict:
    matches = [
        row for row in manifest["outputs"] if row["phase"] == phase and row["rater"] == rater
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one workbook record for {phase}/{rater}")
    return matches[0]


def build_document(rater_key: str, info: dict, manifest: dict) -> Path:
    training = file_record(manifest, "training", rater_key)
    qualification = file_record(manifest, "qualification", rater_key)
    doc = Document()
    configure_document(doc, info["name"], info["role"])

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run(f"Инструкция аннотатора {info['role']}")
    remove_paragraph_borders(title._p)
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.add_run("Калибровка исследования ошибок казахского языка в локальных LLM").bold = True
    recipient = doc.add_paragraph()
    recipient.alignment = WD_ALIGN_PARAGRAPH.CENTER
    recipient.add_run(f"Получатель  {info['name']}\nПодготовлено  15 ноября 2026 года")

    intro = doc.add_paragraph()
    intro.paragraph_format.space_before = Pt(8)
    intro.paragraph_format.space_after = Pt(8)
    intro.add_run("Твоя задача. ").bold = True
    intro.add_run(
        "Лично и независимо разметить сначала 12 training-ответов, затем 20 новых "
        "qualification-ответов. Не обсуждай конкретные ответы до разрешённого этапа и не "
        "просматривай материалы второго аннотатора. Заполненные оригиналы нужно вернуть Aldiyar "
        "с неизменёнными именами файлов."
    )

    doc.add_heading("Что находится в пакете", level=1)
    add_table(
        doc,
        ["Этап", "Файл", "Объём", "Исходный SHA 256"],
        [
            ["Training", Path(training["path"]).name, "12 ответов", training["sha256"]],
            [
                "Qualification",
                Path(qualification["path"]).name,
                "20 ответов",
                qualification["sha256"],
            ],
        ],
        [1.05, 2.65, 0.85, 2.35],
    )
    paragraph = doc.add_paragraph()
    paragraph.add_run("Важно. ").bold = True
    paragraph.add_run(
        "Исходные хеши подтверждают, что выдан правильный пустой файл. После заполнения хеш "
        "изменится; это нормально. Aldiyar сохранит хеш заполненного оригинала до adjudication."
    )

    doc.add_heading("Обязательный порядок работы", level=1)
    add_numbered(
        doc,
        [
            "Открой только свой training-файл. Не открывай qualification-файл до завершения training.",
            "Заполни все 12 training-ответов независимо. Не спрашивай второго аннотатора, как он разметил конкретный текст.",
            "Сохрани файл под исходным именем и отправь Aldiyar. После возврата файл больше не исправляй.",
            "После того как оба training-файла заморожены, участвуй в общем обсуждении правил и спорных типов ошибок. Обсуждать можно training, но нельзя смотреть workbook второго аннотатора.",
            "Только после разрешения Aldiyar открой свой qualification-файл и независимо заполни 20 ответов. Во время qualification обсуждение конкретных ответов запрещено.",
            "Сохрани qualification под исходным именем, отправь Aldiyar и не редактируй после отправки.",
        ],
    )

    doc.add_heading("Правила независимости", level=1)
    add_bullets(
        doc,
        [
            "Не открывай папку, workbook или скриншоты второго аннотатора.",
            "Не пытайся определить модель и не просматривай private model key, receipts, detector output или автоматические подсказки.",
            "Не изменяй prompt, response, reference card, word count или finish reason. Эти поля защищены публичным integrity manifest.",
            "Не переименовывай листы и колонки, не сортируй строки, не добавляй формулы и не удаляй пустые строки на листе Error events.",
            "Если сомневаешься, используй needs_adjudication. Не согласовывай сомнение со вторым аннотатором до заморозки обоих файлов.",
            "При проблеме с Excel остановись и сообщи Aldiyar; не пересобирай workbook вручную.",
        ],
    )

    doc.add_heading("Лист Responses", level=1)
    paragraph = doc.add_paragraph()
    paragraph.add_run("Для каждой строки обязательно заполни пять флагов. ").bold = True
    paragraph.add_run(
        "Допустимые значения: yes, no или needs_adjudication. Колонку missing_requirements "
        "заполняй текстом, если requirement_missing = yes; при no её можно оставить пустой."
    )
    add_table(
        doc,
        ["Поле", "Когда ставить yes"],
        [
            ["refusal", "Ответ прямо отказывается отвечать или заявляет о невозможности выполнить запрос."],
            ["off_task", "Основное содержание не отвечает на поставленный вопрос."],
            ["requirement_missing", "Не выполнен хотя бы один явный пункт prompt или reference card."],
            ["repetition", "Фраза или утверждение повторяется без новой функции или новой информации."],
            ["fabricated_specificity", "Указаны неподтверждённые цены, расписания, правила, адреса или другие проверяемые конкретные сведения."],
            ["rater_comments", "Необязательное краткое пояснение, которое поможет понять сложный случай. Не пиши предположения о модели."],
        ],
        [1.75, 5.15],
    )

    doc.add_heading("Лист Error events", level=1)
    paragraph = doc.add_paragraph()
    paragraph.add_run("Одна строка означает одну независимую ошибку. ").bold = True
    paragraph.add_run(
        "Выбирай самый маленький непрерывный фрагмент, которому нужна одна коррекция. Повтор той "
        "же ошибки в другом месте является отдельным событием. Если ошибок нет, строки для ответа "
        "не создаются."
    )
    add_table(
        doc,
        ["Колонка", "Как заполнять"],
        [
            ["blind_id", "Точно скопируй ID соответствующего ответа с листа Responses."],
            ["event_id", "Уникальный ID внутри ответа, например E01, E02, E03."],
            ["category", "grammatical, lexical, semantic, code_switching или surface."],
            ["exact_fragment", "Точная непрерывная копия ошибочного фрагмента из response_text."],
            ["start_offset_zero_based", "Индекс первого символа фрагмента; первый символ ответа имеет индекс 0."],
            ["end_offset_exclusive", "Индекс первого символа после фрагмента. Длина фрагмента равна end минус start."],
            ["start_token_one_based", "Номер первого токена фрагмента, начиная с 1; токены разделяются видимыми пробелами."],
            ["end_token_one_based", "Номер последнего токена фрагмента включительно."],
            ["proposed_correction", "Исправленный вариант фрагмента. Поле обязательно."],
            ["rationale", "Краткое конкретное объяснение, почему исходный фрагмент ошибочен. Поле обязательно."],
            ["source", "Источник для проверяемого факта, если он использовался; иначе можно оставить пустым."],
            ["needs_adjudication", "yes, если решение неуверенное или зависит от спорной интерпретации; иначе no."],
        ],
        [1.95, 4.95],
    )

    doc.add_heading("Категории ошибок", level=1)
    add_table(
        doc,
        ["Категория", "Определение"],
        [
            ["grammatical", "Ошибочное словообразование, форма, согласование, управление или синтаксис."],
            ["lexical", "Неподходящее слово или сочетание в грамматически возможной конструкции. Одна стилистическая предпочтительность не является ошибкой."],
            ["semantic", "Утверждение противоречит явному условию prompt или reference card, включая выдуманный конкретный факт."],
            ["code_switching", "Незапрошенный фрагмент не на казахском. Имена, принятые заимствования, идентификаторы и запрошенные цитаты не считаются ошибкой."],
            ["surface", "Орфография, пунктуация, регистр и пробелы. Эти события не входят в primary endpoint."],
        ],
        [1.45, 5.45],
    )
    paragraph = doc.add_paragraph()
    paragraph.add_run("При одном перекрывающемся толковании применяй приоритет: ").bold = True
    paragraph.add_run("code_switching, затем semantic, grammatical и lexical. Не дублируй одно событие в нескольких primary categories.")
    paragraph = doc.add_paragraph()
    paragraph.add_run("Отсутствующий компонент ответа. ").bold = True
    paragraph.add_run(
        "Если ответ не выполнил требование, ставь response-level requirement_missing. Не создавай "
        "semantic event автоматически, если в тексте нет отдельного ошибочного утверждения."
    )

    doc.add_heading("Проверка перед отправкой", level=1)
    add_bullets(
        doc,
        [
            "Во всех строках Responses заполнены пять обязательных флагов.",
            "Для каждого requirement_missing = yes перечислены пропущенные требования.",
            "Каждый exact_fragment буквально совпадает с response_text по указанным offsets.",
            "У всех событий уникальные event_id, допустимые категории, token indices, correction, rationale и yes или no в needs_adjudication.",
            "Исходные read-only поля, названия листов, заголовки и порядок строк не изменены.",
            "Файл сохранён под исходным именем и закрыт до отправки.",
        ],
    )
    paragraph = doc.add_paragraph()
    paragraph.add_run("Хеш на Mac после сохранения:").bold = True
    add_code(doc, f"shasum -a 256 {Path(training['path']).name}")
    paragraph = doc.add_paragraph()
    paragraph.add_run("Хеш в Windows PowerShell:").bold = True
    add_code(doc, f"Get-FileHash .\\{Path(training['path']).name} -Algorithm SHA256")
    paragraph = doc.add_paragraph()
    paragraph.add_run(
        "Для qualification замени имя файла в команде. Отправь Aldiyar сам XLSX и полученную строку SHA-256."
    )

    doc.add_heading("Условия прохождения qualification", level=1)
    paragraph = doc.add_paragraph()
    paragraph.add_run("Решение принимает отчёт agreement, а не субъективное впечатление. ").bold = True
    paragraph.add_run("Нужно одновременно выполнить все четыре порога:")
    add_bullets(
        doc,
        [
            "category-presence agreement не ниже 80 процентов;",
            "Cohen's kappa не ниже 0.60, если показатель определён;",
            "interval Krippendorff alpha для общего числа primary events не ниже 0.67;",
            "exact span-match F1 не ниже 0.60 без допуска на неточные границы.",
        ],
    )
    paragraph = doc.add_paragraph()
    paragraph.add_run("Если хотя бы один порог не пройден, ").bold = True
    paragraph.add_run(
        "команда уточняет rubric и повторяет qualification на других неиспользованных dev-ответах. "
        "Калибровочные ответы никогда не входят в финальные результаты исследования."
    )

    doc.add_heading("Твоя дальнейшая ответственность", level=1)
    doc.add_paragraph(info["future"])
    paragraph = doc.add_paragraph()
    paragraph.add_run("Для защиты ты должен уметь своими словами объяснить: ").bold = True
    paragraph.add_run(
        "research question, дизайн 60 prompts x 4 models, пять категорий событий, смысл blinding, "
        "зачем нужны независимые originals и adjudication, главный результат после его появления, "
        "основное ограничение и почему данные не были сфабрикованы."
    )

    doc.add_heading("Текст подтверждения для Aldiyar", level=1)
    confirmation = (
        f"Я, {info['name']}, лично и независимо заполнил файл [ИМЯ ФАЙЛА] как {info['role']}. "
        "Я не просматривал workbook второго аннотатора, private model key, model labels, receipts "
        "или detector output. Я не изменял read-only поля, названия листов и колонок. После отправки "
        "я не буду редактировать этот оригинал. SHA-256 заполненного файла: [ВСТАВИТЬ ХЕШ]."
    )
    paragraph = doc.add_paragraph(confirmation)
    paragraph.paragraph_format.left_indent = Inches(0.25)
    paragraph.paragraph_format.right_indent = Inches(0.25)
    paragraph.paragraph_format.space_before = Pt(8)
    paragraph.paragraph_format.space_after = Pt(8)
    paragraph = doc.add_paragraph()
    paragraph.add_run("Что вернуть Aldiyar. ").bold = True
    paragraph.add_run(
        "На training-этапе: заполненный training XLSX, его SHA-256 и текст подтверждения. После "
        "разрешения на qualification: заполненный qualification XLSX, новый SHA-256 и отдельное "
        "подтверждение. Не отправляй пустые, переименованные или пересобранные файлы."
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_DIR / f"{info['short_name']}_{info['role'].replace(' ', '')}_Instructions_RU.docx"
    doc.save(output)
    return output


def main() -> None:
    manifest = json.loads((CALIBRATION_DIR / "workbook_manifest.json").read_text(encoding="utf-8"))
    outputs = [build_document(key, info, manifest) for key, info in RATERS.items()]
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
