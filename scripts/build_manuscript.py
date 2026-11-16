#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables" / "Kazakh_LLM_Study_Manuscript.docx"


def set_cell_fill(cell, color: str) -> None:
    props = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), color)
    props.append(shading)


def set_cell_margins(cell, top=100, start=120, bottom=100, end=120) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
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


def add_table(doc: Document, headers: list[str], rows: list[list[str]], widths: list[float]) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.autofit = False
    table.style = "Table Grid"
    header_props = table.rows[0]._tr.get_or_add_trPr()
    header_flag = OxmlElement("w:tblHeader")
    header_flag.set(qn("w:val"), "true")
    header_props.append(header_flag)
    for idx, (cell, text) in enumerate(zip(table.rows[0].cells, headers)):
        cell.width = Inches(widths[idx])
        set_cell_fill(cell, "17324D")
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_margins(cell)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        r.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        r.font.size = Pt(9)
    for row_index, values in enumerate(rows):
        cells = table.add_row().cells
        for idx, (cell, text) in enumerate(zip(cells, values)):
            cell.width = Inches(widths[idx])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)
            if row_index % 2:
                set_cell_fill(cell, "EDF3F7")
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if idx == 0 else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(text)
            r.font.size = Pt(8.5)
    doc.add_paragraph()


def add_body(doc: Document, text: str) -> None:
    for block in [x.strip() for x in text.strip().split("\n\n") if x.strip()]:
        p = doc.add_paragraph()
        p.alignment = (
            WD_ALIGN_PARAGRAPH.LEFT
            if "repository revision" in block and "SHA-256" in block
            else WD_ALIGN_PARAGRAPH.JUSTIFY
        )
        p.paragraph_format.first_line_indent = Inches(0.25)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.line_spacing = 1.08
        p.add_run(block)


def clean_markdown(text: str) -> str:
    return re.sub(r"\*\*(.*?)\*\*", r"\1", text).replace("`", "")


def add_hanging_item(doc: Document, marker: str, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.12)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.08
    p.add_run(f"{marker}  ")
    p.add_run(clean_markdown(text))


def add_markdown_appendix(doc: Document, path: Path, heading: str) -> None:
    doc.add_heading(heading, level=1)
    lines = path.read_text(encoding="utf-8").splitlines()
    i = 0
    paragraph_parts: list[str] = []

    def flush_paragraph() -> None:
        if not paragraph_parts:
            return
        p = doc.add_paragraph(clean_markdown(" ".join(paragraph_parts)))
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(4)
        paragraph_parts.clear()

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            flush_paragraph()
            i += 1
            continue
        if line.startswith("# "):
            flush_paragraph()
            i += 1
            continue
        if line.startswith("## "):
            flush_paragraph()
            heading_text = clean_markdown(line[3:])
            heading_paragraph = doc.add_heading(heading_text, level=2)
            if heading_text == "Cross-question rule":
                heading_paragraph.paragraph_format.page_break_before = True
            i += 1
            continue
        if line.startswith("|"):
            flush_paragraph()
            table_lines: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            parsed = [[clean_markdown(cell.strip()) for cell in row.strip("|").split("|")] for row in table_lines]
            if len(parsed) >= 3:
                headers = parsed[0]
                data = [row for row in parsed[2:] if len(row) == len(headers)]
                widths = [5.9 / len(headers)] * len(headers)
                add_table(doc, headers, data, widths)
            continue
        bullet = re.match(r"^-\s+(.*)$", line)
        numbered = re.match(r"^(\d+)\.\s+(.*)$", line)
        if bullet or numbered:
            flush_paragraph()
            marker = "•" if bullet else f"{numbered.group(1)}."
            item = bullet.group(1) if bullet else numbered.group(2)
            i += 1
            continuation = [item]
            while i < len(lines):
                next_line = lines[i].strip()
                if not next_line:
                    break
                if next_line.startswith(("#", "|", "- ")) or re.match(r"^\d+\.\s+", next_line):
                    break
                continuation.append(next_line)
                i += 1
            add_hanging_item(doc, marker, " ".join(continuation))
            continue
        if line.startswith("```"):
            flush_paragraph()
            i += 1
            continue
        paragraph_parts.append(line)
        i += 1
    flush_paragraph()


def add_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.extend([fld_char1, instr, fld_char2])


def main() -> None:
    summary = json.loads(
        (ROOT / "results/derived/final_test_v2/summary.json").read_text(encoding="utf-8")
    )
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.9)
    section.right_margin = Inches(0.9)
    section.header_distance = Inches(0.3)
    section.footer_distance = Inches(0.3)
    add_page_number(section.footer.paragraphs[0])

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    for name, size in (("Title", 24), ("Heading 1", 15), ("Heading 2", 12)):
        style = styles[name]
        style.font.name = "Arial"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Arial")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial")
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.bold = True
    title_style_properties = styles["Title"]._element.get_or_add_pPr()
    title_style_border = title_style_properties.find(qn("w:pBdr"))
    if title_style_border is not None:
        title_style_properties.remove(title_style_border)

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("Evaluating Kazakh Language Errors in Local Large Language Models")
    title_properties = title._p.get_or_add_pPr()
    title_border = title_properties.find(qn("w:pBdr"))
    if title_border is not None:
        title_properties.remove(title_border)
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.add_run("A reproducible four-model protocol for educational and public-information responses").italic = True
    authors = doc.add_paragraph()
    authors.alignment = WD_ALIGN_PARAGRAPH.CENTER
    authors.add_run("Aldiyar Zhaksylyk   Yerkebulan Rakhymbay   Iliyas Aitzhan\nSE-2417   2026").bold = True

    doc.add_heading("Abstract", level=1)
    add_body(doc, f"""
Kazakh language generation remains difficult to evaluate because broad multilingual benchmarks rarely identify the concrete linguistic defects that make an answer unreliable for education or public information. We compare Qwen 3 8B, Llama 3.1 8B, Gemma 3 12B and the Kazakhstan-adapted KazLLM 8B as Q4_K_M artifacts in Ollama on one Apple M4 MacBook Air. Each model answers the same 60 Kazakh educational and public-information prompts under frozen decoding controls, producing 240 source-bound receipts. A three-person team reviewed AI-assisted draft labels in blinded responses, yielding one consensus gold set rather than independent-rater evidence. Primary error rates differed among models (permutation Friedman statistic = {summary['h1']['friedman_statistic']:.2f}, p = {summary['h1']['p_value']:.5f}, Kendall's W = {summary['h1']['kendalls_w']:.3f}). KazLLM had the lowest mean response rate at {summary['models'][3]['all_defined_mean_response_rate']:.2f} events per 100 words and improved on Llama by {-summary['h2']['kazllm_minus_llama']:.2f} events per 100 words (Llama minus KazLLM; 95% bootstrap interval {abs(summary['h2']['ci_high']):.2f} to {abs(summary['h2']['ci_low']):.2f}; Holm-adjusted p = {summary['h2']['p_holm']:.5f}). Semantic errors were the most frequent category among the three general-purpose models, while code-switching was rare. A hybrid Latin-script and fastText detector increased F1 from {summary['h4']['latin']['f1']:.3f} to {summary['h4']['hybrid']['f1']:.3f}, but its bootstrap interval for the improvement included zero. The results apply to the frozen artifacts, prompts and runtime; AI-assisted consensus and pervasive length truncation limit generalization.
""")
    p = doc.add_paragraph()
    p.add_run("CCS Concepts: ").bold = True
    p.add_run("Computing methodologies Natural language generation; Empirical studies in natural language processing; Software and its engineering Reproducibility")
    p = doc.add_paragraph()
    p.add_run("Keywords: ").bold = True
    p.add_run("low-resource evaluation, error analysis, code-switching, reproducibility, human annotation")

    doc.add_heading("1 Introduction", level=1)
    add_body(doc, """
Large language models can produce fluent text in widely represented languages while remaining unstable in languages with smaller digital corpora. Kazakh is especially informative because it combines agglutinative morphology, productive case marking, Cyrillic orthography, extensive contact with Russian and rapidly changing digital usage. A response may look readable yet contain agreement errors, unsuitable lexical combinations, unsupported factual claims or unrequested Russian and English spans. These errors matter in educational explanations and public-information guidance, where apparent fluency can hide a wrong relationship, an invented rule or a misleading instruction [2].

Recent Kazakh benchmarks have improved the evidence base. KazMMLU measures knowledge in Kazakh, Russian and Kazakhstan-specific regional domains [23]. Do LLMs Speak Kazakh provides a pilot comparison of several models [14], and Sherkala-Chat documents the construction of a strong Kazakh conversational model [11]. These studies establish that model choice matters, but they do not answer the narrower question used here: under identical local generation controls, which linguistic error events appear in short practical responses and how often do they occur relative to answer length? The distinction is important. Multiple-choice accuracy does not reveal whether a generated explanation uses the wrong case ending, switches language unnecessarily or invents a specific municipal schedule.

The four earlier course assignments approached this topic from different stages and formatting conventions. They also preserved only three pilot outputs although one report described a larger pilot. The present project therefore treats those documents as provenance rather than as confirmatory evidence. It rebuilds the study from a single protocol, a new test set and machine-verifiable receipts. Historical claims that cannot be traced to raw files do not enter the final analysis.

The evaluation unit is deliberately concrete. A response is not judged by a single impression of fluency. Instead, annotators identify the smallest correctable spans, assign one primary category to each event, record response-level failures and preserve the source text unchanged. Normalizing event counts by word tokens separates error frequency from answer length without pretending that all words are equally difficult. The paired prompt block then supports a within-item model comparison: the four systems answer the same request under the same decoding settings, so prompt difficulty is not confused with model identity.

Local execution is part of the research question rather than an implementation convenience. Students, public institutions and small research groups often evaluate models on hardware they can audit and afford. Quantized local artifacts differ from hosted products in weights, templates, safety layers and update schedules. Recording the exact binary identity, runtime template and generation request therefore defines the treatment being studied. A conclusion about one local artifact is narrower than a claim about an entire model family, but it is also reproducible in a way that a mutable remote endpoint may not be.

The study asks whether total primary-error rates differ among four locally runnable model configurations, whether KazLLM improves on its Llama-family comparison model, whether code-switching dominates other error categories in general-purpose models and whether a hybrid automatic detector improves on a simple Latin-script rule. H1 and H2 are confirmatory. H3 and H4 are exploratory because category dominance and detector performance depend more strongly on the chosen prompts and annotation conventions.

The project makes four explicit contributions: (1) a controlled local generation protocol with immutable artifact and request receipts; (2) a balanced 60-item Kazakh prompt resource with frozen reference cards; (3) a blinded joint-team, AI-assisted span-level error review process with explicit provenance; and (4) an auditable paired statistical plan with fail-closed collection safeguards. It does not claim that four quantized artifacts represent all available models, that purposeful prompts estimate the prevalence of errors in all Kazakh communication, or that joint review measures independent human reliability. The intended contribution is a transparent comparison whose limitations remain visible.
""")

    doc.add_heading("2 Related work", level=1)
    add_body(doc, """
Multilingual evaluation has expanded from translated classification tasks to broad suites that test knowledge, reasoning and generation. XTREME-R compares cross-lingual transfer across many languages [21], and multitask finetuning improves crosslingual generalization [15]. NLLB and FLORES support multilingual translation evaluation [4, 8]. BLOOM provides an open multilingual scaling reference [22], while GPT-4 and HELM illustrate broad capability and scenario-based evaluation [18, 13]. PromptSource also shows the value of explicit, reusable task specifications [25]. These resources improve coverage, but a score alone rarely explains the linguistic mechanism behind a failure.

For Kazakh, language-specific work provides a more appropriate reference point. Maxutov and colleagues found large differences across seven models and emphasized that Kazakh quality cannot be inferred from English performance [14]. KazMMLU added regional knowledge that translated international benchmarks miss [23]. Sherkala-Chat showed that careful data construction and model adaptation can produce strong Kazakh conversational performance without the resources available for English [11]. The ISSAI KazLLM artifact used here is a quantized release intended for local inference [10]. This project compares it with three general-purpose model families while recording the exact file digest and runtime template.

The selected journal has recently published closely related work on a task-specific Vietnamese summarization model [26], a Tibetan large language model [27] and a fine-grained Chinese mathematical evaluation benchmark [28]. Together these articles show that the venue accepts resource, model and benchmark contributions for Asian languages. The present study differs by emphasizing controlled local inference, error-event annotation and paired statistical comparison for Kazakh rather than model training or task accuracy alone.

Model evaluation in a low-resource language also raises a measurement problem. Automatic overlap metrics reward similarity to a reference wording, yet a practical explanation may be correct in many forms and a fluent answer may still invent a local rule. Purpose-designed reference cards are therefore more suitable here than a single gold response: they state required propositions, acceptable variants and prohibited unsupported specifics while leaving surface realization open. This approach increases annotation effort, but it makes semantic judgments auditable and avoids treating harmless paraphrase as an error.

Quantization and local serving create additional sources of variation that are easy to omit from a paper. Two artifacts with the same parameter count can differ in quantizer, chat template, stop handling and runtime defaults. Even a mutable tag can point to different content over time. The present comparison does not attempt to decompose these factors causally. Instead, it treats each complete artifact-plus-template configuration as the experimental condition and records enough metadata for another machine to reconstruct that condition. This choice favors ecological reproducibility over an architectural ablation.

Error analysis requires a unit that annotators can apply consistently. Traditional machine-translation metrics such as BLEU summarize output quality but do not localize the linguistic mechanism of an error [19]. The present rubric therefore uses four primary categories relevant to Kazakh generation. Grammatical events cover morphology and syntax. Lexical events cover unsuitable word choice when the proposition remains recoverable. Semantic events cover contradictions with the prompt or verified reference card. Code-switching covers unrequested foreign-language spans after explicit exemptions. Surface spelling and punctuation remain secondary because the primary hypothesis concerns errors that change structure, choice, meaning or language.

Reliable annotation needs more than a written label list [1]. Cohen's kappa measures nominal agreement beyond chance [3], while Krippendorff's alpha supports broader measurement levels and missing observations [12]. Those statistics require genuinely independent judgments. The instructor-authorized workflow used here instead produces one joint team-consensus gold set with AI-assisted drafts, immutable source binding and a per-response review log. It therefore does not report kappa, alpha or span F1 as human reliability evidence; that loss of independent reliability measurement is an explicit limitation.

The statistical design follows the paired structure of the experiment. Every prompt forms a block observed under all four models. Friedman's rank test is appropriate for repeated nonparametric comparisons [5, 7], but the project uses a permutation version to preserve the planned finite-sample interpretation. Pairwise signed-rank comparisons follow Wilcoxon [24] and Pratt's zero-retaining variant [20], while Holm's procedure controls family-wise error across six comparisons [9]. Whole-prompt bootstrap resampling preserves the cluster of four model responses generated from one prompt and supports intervals for mean paired differences and detector F1 contrasts [6].
""")
    add_table(doc, ["Study", "Language / scope", "Evidence", "Gap retained here"], [
        ["Maxutov et al. [14]", "Kazakh; seven models", "Pilot model comparison", "No frozen event-level paired protocol"],
        ["KazMMLU [23]", "Kazakh/Russian; regional knowledge", "Multiple-choice benchmark", "Does not localize generation errors"],
        ["Sherkala-Chat [11]", "Kazakh conversational model", "Model/data construction", "Not a four-artifact local error comparison"],
        ["This study", "Kazakh practical generation", "60 prompts, 240 paired responses, joint team gold", "No independent-rater reliability estimate"],
    ], [1.35, 1.45, 1.55, 1.55])

    doc.add_heading("3 Methods", level=1)
    doc.add_heading("3.1 Models and environment", level=2)
    add_body(doc, """
The study runs four Q4_K_M model configurations in Ollama 0.33.3 on an Apple M4 MacBook Air with 24 GB unified memory. The comparison includes Qwen 3 8B, Llama 3.1 8B, Gemma 3 12B and KazLLM 8B. Equal quantization labels reduce one source of variation but do not make the systems equivalent. Gemma has more parameters, each family uses a different tokenizer and prompt template, and the KazLLM release adapts a Llama-family base to Kazakh. Conclusions therefore apply to the exact tested artifacts rather than to every version of each family.

Mutable model tags are insufficient for reproducibility. Before collection, the repository records the Ollama content digest, byte size, format, family, parameter size, quantization level, template hash, parameters hash and system-prompt hash. The official gated KazLLM GGUF is pinned to repository revision eb04ab55b920c64dc50583f20de783e1d3034529 and SHA-256 1a37de3ca5e9fb3754ac070f8a5d1dc328c2ac43217daea506bf1877fab76dba. The model binary is not committed because of size and licensing conditions.
""")
    add_table(doc, ["Model", "Digest prefix", "Size", "Quantization"], [
        ["Qwen 3 8B", "500a1f067a9f", "5.2 GB", "Q4_K_M"],
        ["Llama 3.1 8B", "46e0c10c039e", "4.9 GB", "Q4_K_M"],
        ["Gemma 3 12B", "b92b218582c5", "8.2 GB", "Q4_K_M"],
        ["KazLLM 8B", "2dacc6fb6467", "4.9 GB", "Q4_K_M"],
    ], [1.6, 1.8, 1.1, 1.4])

    doc.add_heading("3.2 Prompt set", level=2)
    add_body(doc, """
The test set contains 60 newly drafted Kazakh prompts. Thirty educational prompts cover natural science, mathematics and data, history and society, language and media literacy, and computing and technology. Thirty public-information prompts cover municipal services, transport and accessibility, cultural and educational spaces, environmental and household safety, and digital consumer literacy. Within each task type, five domains are crossed with six task forms exactly once. This creates 30 unique domain-form cells per task type and prevents one form from dominating a domain.

The educational forms are definition, cause and effect, comparison, step-by-step explanation, application and misconception correction. Public-information forms are first contact, preparation checklist, problem resolution, safe and respectful behavior, local-condition verification and neutral public notice. Validation checks exact columns, unique identifiers, duplicate normalized text, matrix balance and similarity with the 20 development prompts. The development prompts support calibration and technical smoke tests and never enter confirmatory results.

Every prompt has a reference or constraint card. The card records required content, acceptable variants, prohibited unsupported claims and authoritative sources when factual verification is necessary. The cards are frozen before test generation so annotators do not revise standards after seeing model outputs. A reference card does not prescribe one ideal wording. It defines the factual and task constraints needed for semantic and requirement-missing judgments.

Prompt construction follows a documented review sequence. Each item is checked for natural Kazakh wording, one clear task, answerability without personal data, independence from volatile prices or schedules, and suitability for a 150–200-word response. Reviewers also inspect whether a named organization or location would force a model to guess. When local conditions can change, the prompt asks the model to explain how to verify them rather than to invent a current value. The validation script then checks identifiers, exact columns, empty fields, normalized duplicates, domain-form balance and similarity leakage from the development set. Human review remains necessary because structural validation cannot determine whether a sentence is idiomatic or factually fair.
""")

    doc.add_heading("3.3 Generation procedure", level=2)
    add_body(doc, """
Each request contains one user message consisting of a common Kazakh instruction followed by the prompt. The instruction asks for a clear answer in Kazakh of approximately 150 to 200 words, prohibits requests for personal data and prohibits invented institution-specific rules, prices or schedules. Every model-prompt pair starts a fresh conversation through the Ollama chat interface [17]. Generation uses temperature 0, seed 2417, num_predict 768, num_ctx 4096, top_k 40, top_p 1, repeat_penalty 1, think false, stream false and keep_alive 0. The request order is shuffled once with seed 2417.

The collector writes an inflight marker before contacting Ollama. A completed receipt can be reused only when the saved request equals the new request. An ambiguous timeout blocks automatic retry because a retry could produce a cleaner answer and bias the sample. Empty, refused, repetitive, off-task and length-truncated outputs remain part of the accounted experiment. The collector compares model metadata before and after the run and fails if any artifact changes.
""")

    doc.add_heading("3.4 Annotation", level=2)
    add_body(doc, """
The three authors jointly review one blinded annotation workbook. They see the prompt, response and frozen card but not model identity, timing information or detector candidates. The locally installed qwen3:8b artifact may propose compact draft flags and at most two high-confidence event candidates without access to the private model mapping. Every proposed event is marked for adjudication, and the final gold set requires a review-log entry naming the responsible team member for every blind response. The private model key opens only after the workbook and review log are frozen. This workflow is disclosed as joint AI-assisted review, not independent annotation.

An error event is the smallest continuous fragment requiring one independent correction. Annotators record the exact fragment, zero-based half-open character offsets, inclusive token indices, proposed correction, rationale and any source used. Overlap priority is code-switching, semantic, grammatical and lexical. Repeated occurrences at different locations count separately. Spelling, punctuation, capitalization and spacing are surface events and do not increase the primary rate.

Response-level fields capture refusal, off-task content, missing requirements, repetition and fabricated specificity. Word count, length compliance and truncation come from raw text and Ollama receipts rather than subjective judgment. Twelve development responses and 20 disjoint qualification responses are retained for schema training and rubric checks. Because those files were completed jointly with AI assistance, perfect agreement between duplicate transport copies is not interpreted as reliability or qualification evidence.

The workbook design separates observation from model identity. Each response receives a stable anonymous identifier; model names, timings and detector outputs are excluded. Required fields and data validation reduce schema drift. The review log records the responsible team member, review status, AI-assistance disclosure and timestamp for every response. These controls do not create independence or eliminate shared judgment, but they make the final gold set traceable and protect detector evaluation from direct label leakage.
""")

    doc.add_heading("3.5 Statistical analysis", level=2)
    add_body(doc, """
For each non-empty response, the primary endpoint equals 100 multiplied by the reviewed team-gold count of grammatical, lexical, semantic and code-switching events divided by word tokens. A zero-word response has an undefined rate and is reported as a generation failure. The primary Friedman analysis uses only prompt blocks with defined rates for all four models. Truncated outputs remain in the main analysis and are excluded only in a sensitivity analysis.

H1 uses a tie-corrected Friedman statistic with 99,999 within-prompt label permutations and seed 2417. Kendall's W reports the omnibus effect size. Six two-sided pairwise Pratt signed-rank permutation tests receive Holm adjustment. For each pair the report includes rank-biserial correlation and the mean response-rate difference with a 95 percent interval from 10,000 whole-prompt bootstrap resamples stratified by task type.

H2 receives support only if H1 is significant, the Holm-adjusted KazLLM-Llama comparison is significant, the KazLLM minus Llama point estimate is negative and its bootstrap interval lies entirely below zero. Failure to satisfy these conditions means the study does not support H2. It does not establish equivalence.

H3 pools reviewed events and word tokens across Qwen, Llama and Gemma. Category rates are reported per 100 words with prompt-bootstrap intervals. H4 defines a gold code-switching positive as any response with at least one reviewed code-switching event. The Latin baseline detects a non-exempt word token containing a Latin letter. The fastText component follows efficient text-classification practice [16], testing sentences and sliding three-word windows at confidence 0.85; the hybrid prediction is the union of Latin and fastText positives. Precision, recall and F1 use all 240 responses, with a whole-prompt bootstrap interval for hybrid minus Latin F1.

Pre-specified sensitivity analyses protect the interpretation from avoidable analytic flexibility. The first excludes truncated responses while keeping the same prompt-block rule. The second reports unnormalized primary-event counts alongside rates so a length-driven reversal is visible. The third separates educational and public-information prompts descriptively without promoting subgroup comparisons to new confirmatory hypotheses. Zero-word outputs are accounted for as generation failures rather than assigned an arbitrary infinite or zero rate. Missing blocks, permutation seeds, resample counts and every exclusion are reported in generated metadata so a reader can reconstruct the exact analysis population.
""")

    doc.add_heading("4 Executed collection and validation evidence", level=1)
    add_body(doc, """
The repository demonstrates complete collection, source binding and technical validation for the model comparison reported below. The final run contains 240 validated receipts with identical controls and unchanged model metadata. One Gemma request initially failed because its Ollama runner did not load before the server deadline; the original in-flight record and incident record are retained, and an identical-payload infrastructure retry succeeded before any response existed. No output was regenerated for quality. The automated test suite passes locally and in the public CI workflow. It covers prompt validation, stable request construction, receipt reuse, ambiguous-request blocking, workbook blinding, detector behavior, binary metrics, clustered F1 resampling, Friedman components, permutation behavior, Pratt comparisons, Holm adjustment and bootstrap differences. The 60 test prompts pass the exact balance matrix and no development prompt crosses the configured similarity threshold.

All four required models pass an Ollama preflight that checks installation, digest availability and Q4_K_M quantization. One retained development smoke response exists for each model under the intended generation controls. Llama reached the 768-token boundary and repeated content; the run preserves this failure instead of regenerating it. KazLLM returned 109 words with a normal stop. A two-request Qwen check produced identical response SHA-256 values. These observations confirm that the local stack executes the planned requests and retains undesirable outputs.

The repository also captures the Mac hardware summary, operating environment, Python lock file, Ollama version, external language-identification resource hashes and the pinned Universal Dependencies Kazakh treebank resource. Secret scans exclude access tokens, private blinding keys, model binaries and local virtual environments. The test collector accepts the test set only when every frozen prompt, protocol, authorization, exemption and model-artifact hash still matches. This lock is an intended safeguard, not a software failure.
""")

    doc.add_heading("5 Results", level=1)
    add_body(doc, f"""
All 240 requests produced retained, source-bound receipts and all 60 prompt blocks had defined primary-error rates for all four models. One pre-generation Gemma runner-load failure was resolved by the documented identical-payload infrastructure retry before any response existed. The immutable receipts identify 98 length-truncated responses: 52 for Llama, 42 for KazLLM and 4 for Qwen. The primary analysis retained these outputs as prespecified. Because every prompt block contained at least one truncated response, the exclusion sensitivity analysis had zero complete blocks and was not estimable.

The final workbook contains 855 reviewed events and 240 approved response records. Each of the three authors was assigned 80 responses. AI suggestions were treated as drafts; the coordinator entered the approval records after the assigned reviewers confirmed them. This process yields a joint team-consensus gold set and cannot support an inter-annotator reliability estimate.
""")

    model_rows = []
    model_names = {
        "qwen3_8b": "Qwen 3 8B",
        "llama31_8b": "Llama 3.1 8B",
        "gemma3_12b": "Gemma 3 12B",
        "kazllm_8b": "KazLLM 8B",
    }
    short_model_names = {
        "qwen3_8b": "Qwen",
        "llama31_8b": "Llama",
        "gemma3_12b": "Gemma",
        "kazllm_8b": "KazLLM",
    }
    for row in summary["models"]:
        model_rows.append([
            model_names[row["model"]],
            str(row["total_primary_events"]),
            str(row["total_words"]),
            f"{row['all_defined_mean_response_rate']:.2f}",
            f"{row['all_defined_median_response_rate']:.2f}",
            f"{row['cluster_ci_low']:.2f}–{row['cluster_ci_high']:.2f}",
        ])
    add_table(
        doc,
        ["Model", "Events", "Words", "Mean rate", "Median rate", "95% prompt CI"],
        model_rows,
        [1.15, 0.65, 0.65, 0.9, 0.95, 1.6],
    )

    add_body(doc, f"""
The pre-specified omnibus test supported H1: model rates differed across the 60 paired prompt blocks (permutation Friedman statistic = {summary['h1']['friedman_statistic']:.2f}, p = {summary['h1']['p_value']:.5f} with {summary['h1']['permutations']:,} permutations; Kendall's W = {summary['h1']['kendalls_w']:.3f}). KazLLM had the lowest mean response rate, followed by Gemma, Llama and Qwen. H2 was also supported. KazLLM's mean rate was {abs(summary['h2']['kazllm_minus_llama']):.2f} events per 100 words lower than Llama's (95% whole-prompt bootstrap interval {abs(summary['h2']['ci_high']):.2f} to {abs(summary['h2']['ci_low']):.2f}; Holm-adjusted p = {summary['h2']['p_holm']:.5f}).
""")

    pairwise_rows = []
    for row in summary["pairwise"]:
        pairwise_rows.append([
            f"{short_model_names[row['left']]} – {short_model_names[row['right']]}",
            f"{row['difference']:.2f}",
            f"{row['ci_low']:.2f}–{row['ci_high']:.2f}",
            f"{row['p_holm']:.5f}",
        ])
    add_table(
        doc,
        ["Contrast", "Mean difference", "95% prompt CI", "Holm p"],
        pairwise_rows,
        [2.0, 1.1, 1.65, 1.15],
    )

    h3 = summary["h3"]["category_summaries"]
    add_body(doc, f"""
H3 was not supported. Among Qwen, Llama and Gemma, semantic errors had the highest pooled rate ({h3['semantic']['pooled_rate_per_100_words']:.2f} per 100 words), followed by lexical ({h3['lexical']['pooled_rate_per_100_words']:.2f}), grammatical ({h3['grammatical']['pooled_rate_per_100_words']:.2f}) and code-switching ({h3['code_switching']['pooled_rate_per_100_words']:.3f}). The prompt-bootstrap interval for every code-switching-minus-other-category contrast was wholly below zero, so code-switching was the least frequent rather than the dominant primary category.

H4 was not supported by the uncertainty analysis. The Latin baseline detected only one of seven gold-positive responses and had F1 = {summary['h4']['latin']['f1']:.3f}. The hybrid detector detected six of seven but produced 72 false positives, yielding precision = {summary['h4']['hybrid']['precision']:.3f}, recall = {summary['h4']['hybrid']['recall']:.3f} and F1 = {summary['h4']['hybrid']['f1']:.3f}. Its F1 improvement over the Latin baseline was {summary['h4']['hybrid_minus_latin']['difference']:.3f}, with a 95% prompt-bootstrap interval from {summary['h4']['hybrid_minus_latin']['ci_low']:.3f} to {summary['h4']['hybrid_minus_latin']['ci_high']:.3f}; the interval crossed zero.
""")
    add_table(
        doc,
        ["Detector", "TP", "FP", "FN", "Precision", "Recall", "F1"],
        [
            [
                "Latin",
                str(summary["h4"]["latin"]["tp"]),
                str(summary["h4"]["latin"]["fp"]),
                str(summary["h4"]["latin"]["fn"]),
                f"{summary['h4']['latin']['precision']:.3f}",
                f"{summary['h4']['latin']['recall']:.3f}",
                f"{summary['h4']['latin']['f1']:.3f}",
            ],
            [
                "fastText",
                str(summary["h4"]["fasttext"]["tp"]),
                str(summary["h4"]["fasttext"]["fp"]),
                str(summary["h4"]["fasttext"]["fn"]),
                f"{summary['h4']['fasttext']['precision']:.3f}",
                f"{summary['h4']['fasttext']['recall']:.3f}",
                f"{summary['h4']['fasttext']['f1']:.3f}",
            ],
            [
                "Hybrid",
                str(summary["h4"]["hybrid"]["tp"]),
                str(summary["h4"]["hybrid"]["fp"]),
                str(summary["h4"]["hybrid"]["fn"]),
                f"{summary['h4']['hybrid']['precision']:.3f}",
                f"{summary['h4']['hybrid']['recall']:.3f}",
                f"{summary['h4']['hybrid']['f1']:.3f}",
            ],
        ],
        [1.2, 0.55, 0.55, 0.55, 1.0, 1.0, 1.05],
    )

    add_body(doc, f"""
Including surface errors in the primary count preserved the omnibus conclusion (Friedman statistic = {summary['sensitivity']['include_surface_errors']['statistic']:.2f}, p = {summary['sensitivity']['include_surface_errors']['p_value']:.5f}, Kendall's W = {summary['sensitivity']['include_surface_errors']['kendalls_w']:.3f}). Most model-by-task difference-in-differences intervals included zero; the only interval excluding zero was Llama minus Gemma, indicating a larger public-versus-educational contrast for that pair. These subgroup results remain descriptive.
""")

    doc.add_heading("6 Discussion", level=1)
    add_body(doc, """
The design favors traceability over breadth. One local machine, one quantized artifact per family and deterministic decoding make the run easier to audit, but the resulting comparison cannot isolate architecture, training data, parameter count, prompt template and quantization as separate causes. Gemma has approximately 12 billion parameters while the other artifacts have about 8 billion. KazLLM and Llama share a family but differ in adaptation and packaging. The lower observed KazLLM error rate describes the complete tested configuration; it does not prove that one training decision caused the difference.

Purposeful prompts support error discovery but do not form a probability sample of Kazakh language use. Educational and public-information tasks were chosen because errors in these settings are interpretable and consequential. The rates should not be generalized to literature, informal messaging, professional translation or long-form reasoning. The single response per model-prompt pair also estimates performance under the frozen deterministic condition, not variability across sampling temperatures or seeds.

The design also separates repeatability from generality. Temperature zero and a fixed seed reduce one source of run-to-run variation, and the determinism check verifies behavior for a retained sample. They do not prove that every backend, operating-system version or accelerator will emit identical bytes, nor do they estimate a distribution over creative generations. The resulting claims concern the frozen Mac/Ollama environment. Replication on another platform would be valuable, but it should be reported as a new environment rather than mixed silently into the primary run.

Joint annotation introduces shared judgment. Reference cards narrow semantic decisions and calibration exposes ambiguous rules, but AI-assisted consensus cannot reveal how often independent humans would disagree and may propagate one systematic error across the gold set. The Qwen draft annotator is itself one of the evaluated artifacts; although it receives no model mapping and every proposal requires human adjudication, its suggestions can still anchor reviewers or express category-specific bias. Blinding also has limits because reviewers may recognize stylistic patterns, and a whole foreign-language response can reveal model tendencies. The protocol prevents direct model labels and timing information from appearing in the workbook but cannot guarantee perfect perceptual blinding.

Automatic code-switching detection is deliberately secondary. A Latin script rule can detect English fragments but misses Russian in Cyrillic and can flag identifiers or accepted borrowings. fastText can capture broader language shifts but may misclassify short Kazakh windows. The hybrid detector is evaluated against the reviewed team gold and detector candidates remain hidden until that gold set is frozen. Because AI assistance is allowed in draft annotation, detector output is still excluded to prevent direct target leakage.

The observed model difference does not establish that one family is universally better. KazLLM's lower event rate identifies it as the strongest tested configuration for these short Kazakh educational and public-information responses under the frozen controls. The category profile points to semantic and lexical errors as larger practical targets than code-switching. Because independent agreement is unavailable, confidence in fine-grained category claims relies on transparent review provenance, the source-bound event records and sensitivity checks rather than a reliability coefficient.

The study evaluates locally generated text and does not intentionally collect external participant data or personal information. The annotators are the authors. The supplied materials contain no evidence of formal ethics approval or exemption, so the paper must not invent an approval number. The team should confirm institutional requirements with the instructor and record the resulting determination before external submission.

The intended venue is ACM Transactions on Asian and Low-Resource Language Information Processing because the paper directly evaluates an Asian low-resource language and emphasizes practical language processing. Language Resources and Evaluation is a defensible backup when the paper foregrounds the released prompt resource, annotation protocol and gold spans. Journal choice does not alter the evidence layer, generated tables or limitations.
""")

    doc.add_heading("7 Conclusion", level=1)
    add_body(doc, """
This project replaces inconsistent assignment-stage documents with one reproducible study. The prompt matrix, exact model artifacts, local environment, collection safeguards, annotation instrument and confirmatory analysis are implemented and tested. Across 60 paired prompts, the models differed significantly, and KazLLM had the lowest reviewed primary-error rate. Its pre-specified improvement over Llama supported H2. Semantic errors, not code-switching, were the dominant category among the general-purpose models, and the apparent hybrid-detector F1 gain remained uncertain. These conclusions are limited to the frozen local artifacts and an AI-assisted joint consensus gold set.

After the primary study is frozen, future work can replicate the protocol on additional hardware, larger or differently quantized artifacts, and naturally sampled Kazakh requests. Those extensions should retain the same provenance and annotation safeguards while treating every changed model, prompt population or runtime as a new experimental condition. The immediate goal remains narrower: complete one defensible comparison whose evidence can be inspected from prompt to claim.
""")

    doc.add_heading("Declarations", level=1)
    doc.add_heading("Data and code availability", level=2)
    add_body(doc, """
The accompanying version-controlled course repository contains the prompt sets, reference cards, frozen protocol, model-artifact manifest, environment capture, immutable test receipts, incident evidence, reviewed team-gold workbook, completed review log, generated result tables, analysis code, tests and document builders. Project-authored code is released under the MIT License; original prompts, protocols and documentation are released under CC BY 4.0. Third-party resources and model artifacts retain their original terms. The gated KazLLM binary and other model weights are not redistributed.
""")
    doc.add_heading("CRediT author contributions", level=2)
    add_body(doc, """
Aldiyar Zhaksylyk: conceptualization, methodology, software, investigation, data curation, reproducibility, project administration and final audit. Yerkebulan Rakhymbay: validation, label quality control, formal analysis and statistical interpretation. Iliyas Aitzhan: team-gold and results integration, writing-review and editing, visualization review and numerical consistency. All authors are required to review and approve the frozen release before submission.
""")
    doc.add_heading("AI-use declaration", level=2)
    add_body(doc, """
OpenAI Codex assisted with software, document drafting, formatting and quality checks under the instructor-authorized joint workflow. The pinned local qwen3:8b artifact generated blinded annotation suggestions with machine-recorded provenance; those suggestions are not approvals and remain subject to assigned human adjudication. The human authors remain responsible for the final gold labels, source verification, statistical interpretation and every submitted claim. The study does not represent AI-assisted team labels as independent human ratings, and AI tools are not authors.
""")
    doc.add_heading("Funding and conflicts of interest", level=2)
    add_body(doc, """
No external funding was reported for this course project. The authors declare no known conflict of interest.
""")
    doc.add_heading("Ethics statement", level=2)
    add_body(doc, """
The study evaluates locally generated model text and does not intentionally collect data from external human participants or personal information. The annotators are the authors. No ethics approval or exemption number is claimed because none was evidenced in the supplied materials. The team must confirm the institution's determination with the instructor before any external journal submission.
""")

    doc.add_heading("References", level=1)
    references = [
        "Artstein, R., and Poesio, M. 2008. Inter-coder agreement for computational linguistics. Computational Linguistics 34, 4, 555-596. https://doi.org/10.1162/coli.07-034-R2",
        "Bender, E. M., Gebru, T., McMillan-Major, A., and Shmitchell, S. 2021. On the dangers of stochastic parrots. FAccT 2021. https://doi.org/10.1145/3442188.3445922",
        "Cohen, J. 1960. A coefficient of agreement for nominal scales. Educational and Psychological Measurement 20, 1, 37-46. https://doi.org/10.1177/001316446002000104",
        "Costa-jussa, M. R. et al. 2022. No Language Left Behind. arXiv:2207.04672. https://doi.org/10.48550/arXiv.2207.04672",
        "Demsar, J. 2006. Statistical comparisons of classifiers over multiple data sets. Journal of Machine Learning Research 7, 1-30. https://jmlr.org/papers/v7/demsar06a.html",
        "Efron, B., and Tibshirani, R. J. 1993. An Introduction to the Bootstrap. Chapman and Hall/CRC.",
        "Friedman, M. 1937. The use of ranks to avoid the assumption of normality implicit in the analysis of variance. JASA 32, 200, 675-701. https://doi.org/10.1080/01621459.1937.10503522",
        "Goyal, N. et al. 2022. The FLORES-101 evaluation benchmark for low-resource and multilingual machine translation. TACL 10, 522-538. https://doi.org/10.1162/tacl_a_00474",
        "Holm, S. 1979. A simple sequentially rejective multiple test procedure. Scandinavian Journal of Statistics 6, 2, 65-70.",
        "ISSAI. 2024. LLama-3.1-KazLLM-1.0-8B-GGUF4 model card. https://huggingface.co/issai/LLama-3.1-KazLLM-1.0-8B-GGUF4",
        "Koto, F. et al. 2025. Sherkala-Chat: Building a state-of-the-art LLM for Kazakh in a moderately resourced setting. arXiv:2503.01493. https://doi.org/10.48550/arXiv.2503.01493",
        "Krippendorff, K. 2011. Computing Krippendorff's alpha-reliability. University of Pennsylvania. https://repository.upenn.edu/asc_papers/43",
        "Liang, P. et al. 2022. Holistic evaluation of language models. arXiv:2211.09110. https://doi.org/10.48550/arXiv.2211.09110",
        "Maxutov, A., Myrzakhmet, A., and Braslavski, P. 2024. Do LLMs speak Kazakh? SIGTURK 2024, 81-91. https://aclanthology.org/2024.sigturk-1.8/",
        "Muennighoff, N. et al. 2023. Crosslingual generalization through multitask finetuning. ACL 2023, 15991-16111. https://doi.org/10.18653/v1/2023.acl-long.891",
        "Joulin, A., Grave, E., Bojanowski, P., and Mikolov, T. 2017. Bag of tricks for efficient text classification. EACL 2017, 427-431. https://doi.org/10.18653/v1/E17-2068",
        "Ollama. 2026. Chat API documentation. https://docs.ollama.com/api/chat",
        "OpenAI et al. 2023. GPT-4 technical report. arXiv:2303.08774. https://doi.org/10.48550/arXiv.2303.08774",
        "Papineni, K., Roukos, S., Ward, T., and Zhu, W. J. 2002. BLEU: a method for automatic evaluation of machine translation. ACL 2002. https://doi.org/10.3115/1073083.1073135",
        "Pratt, J. W. 1959. Remarks on zeros and ties in the Wilcoxon signed rank procedures. JASA 54, 287, 655-667. https://doi.org/10.1080/01621459.1959.10501526",
        "Ruder, S. et al. 2021. XTREME-R: Towards more challenging and nuanced multilingual evaluation. EMNLP 2021, 10215-10245. https://doi.org/10.18653/v1/2021.emnlp-main.802",
        "Scao, T. L. et al. 2023. BLOOM: A 176B-parameter open-access multilingual language model. arXiv:2211.05100. https://doi.org/10.48550/arXiv.2211.05100",
        "Togmanov, M. et al. 2025. KazMMLU: Evaluating language models on Kazakh, Russian, and regional knowledge of Kazakhstan. ACL 2025, 14403-14416. https://doi.org/10.18653/v1/2025.acl-long.701",
        "Wilcoxon, F. 1945. Individual comparisons by ranking methods. Biometrics Bulletin 1, 6, 80-83. https://doi.org/10.2307/3001968",
        "Zhang, S. et al. 2023. PromptSource: An integrated development environment and repository for natural language prompts. ACL 2022 System Demonstrations, 93-104. https://doi.org/10.18653/v1/2022.acl-demo.9",
        "Le, T. A., and Le, H. S. 2025. LatVis: Large-scale task-specific language model for low-resource Vietnamese multi-document summarization. ACM TALLIP 24, 5, 1-19. https://doi.org/10.1145/3725848",
        "Sha, J., Zhu, M., Feng, C., and Ci, J. 2025. Tibetan-LLaMA 2: Large language model for Tibetan. ACM TALLIP 24, 12, 1-19. https://doi.org/10.1145/3776748",
        "Liu, Y., Jin, R., Shi, L., Yao, Z., and Xiong, D. 2025. FineMath: A fine-grained mathematical evaluation benchmark for Chinese large language models. ACM TALLIP 24, 12, 1-15. https://doi.org/10.1145/3773083",
    ]
    for i, ref in enumerate(references, 1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.first_line_indent = Inches(-0.25)
        p.paragraph_format.space_after = Pt(3)
        p.add_run(f"[{i}] {ref}")

    add_markdown_appendix(doc, ROOT / "docs/JOURNAL_FIT_STATEMENT.md", "Appendix A Journal Fit Statement")
    add_markdown_appendix(doc, ROOT / "docs/RELEASE_CHECKLIST.md", "Appendix B Submission Readiness Checklist")
    add_markdown_appendix(doc, ROOT / "protocol/annotation_protocol.md", "Appendix C Annotation Protocol")
    add_markdown_appendix(doc, ROOT / "docs/DEFENSE_PLAN.md", "Appendix D Contribution and Defense Plan")

    core = doc.core_properties
    core.title = "Evaluating Kazakh Language Errors in Local Large Language Models"
    core.subject = "Reproducible four-model Kazakh LLM evaluation protocol"
    core.author = "Aldiyar Zhaksylyk; Yerkebulan Rakhymbay; Iliyas Aitzhan"
    core.keywords = "Kazakh, LLM, error analysis, reproducibility"
    core.comments = "Prepared for the SE-2417 course defense from the frozen final analysis."

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    words = sum(len(re.findall(r"\b[\w'-]+\b", p.text)) for p in doc.paragraphs)
    print(f"{OUT}\nword_count={words}\nparagraphs={len(doc.paragraphs)}")


if __name__ == "__main__":
    main()
