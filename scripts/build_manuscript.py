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

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("Evaluating Kazakh Language Errors in Local Large Language Models")
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.add_run("A reproducible four-model protocol for educational and public-information responses").italic = True
    authors = doc.add_paragraph()
    authors.alignment = WD_ALIGN_PARAGRAPH.CENTER
    authors.add_run("Aldiyar Zhaksylyk   Yerkebulan Rakhymbay   Iliyas Aitzhan\nSE-2417   2026").bold = True

    doc.add_heading("Abstract", level=1)
    add_body(doc, """
Kazakh language generation remains difficult to evaluate because broad multilingual benchmarks rarely identify the concrete linguistic defects that make an answer unreliable for education or public information. This study defines a reproducible local comparison of Qwen 3 8B, Llama 3.1 8B, Gemma 3 12B and the Kazakhstan-adapted KazLLM 8B. All four configurations use Q4_K_M artifacts in Ollama on one Apple M4 MacBook Air. The protocol contains 60 newly drafted Kazakh prompts, balanced between educational and public-information tasks and crossed by domain and task form. Each model receives every prompt once with temperature zero, seed 2417, a fresh one-message conversation and fixed decoding controls. Two independent annotators classify grammatical, lexical, semantic and code-switching events in 240 blinded responses. A third author adjudicates disagreements before the model key is opened. The primary endpoint is the number of adjudicated primary events per 100 word tokens. Confirmatory analysis uses a permutation Friedman test, Kendall's W, Holm-adjusted Pratt signed-rank comparisons and whole-prompt bootstrap intervals. The repository already verifies the prompt matrix, exact model artifacts, environment, collection safeguards, annotation workbooks, detector logic and statistical functions. Final model-ranking claims remain gated until the team freezes the reference cards, collects all test receipts and completes both independent annotations. This separation prevents technical readiness evidence from being reported as a linguistic result.
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

The project makes four explicit contributions: (1) a controlled local generation protocol with immutable artifact and request receipts; (2) a balanced 60-item Kazakh prompt resource with frozen reference cards; (3) a blinded two-rater span-level error annotation process; and (4) an auditable paired statistical plan with fail-closed collection safeguards. It does not claim that four quantized artifacts represent all available models or that purposeful prompts estimate the prevalence of errors in all Kazakh communication. The intended contribution is a transparent comparison whose limitations remain visible.
""")

    doc.add_heading("2 Related work", level=1)
    add_body(doc, """
Multilingual evaluation has expanded from translated classification tasks to broad suites that test knowledge, reasoning and generation. XTREME-R compares cross-lingual transfer across many languages [21], and multitask finetuning improves crosslingual generalization [15]. NLLB and FLORES support multilingual translation evaluation [4, 8]. BLOOM provides an open multilingual scaling reference [22], while GPT-4 and HELM illustrate broad capability and scenario-based evaluation [18, 13]. PromptSource also shows the value of explicit, reusable task specifications [25]. These resources improve coverage, but a score alone rarely explains the linguistic mechanism behind a failure.

For Kazakh, language-specific work provides a more appropriate reference point. Maxutov and colleagues found large differences across seven models and emphasized that Kazakh quality cannot be inferred from English performance [14]. KazMMLU added regional knowledge that translated international benchmarks miss [23]. Sherkala-Chat showed that careful data construction and model adaptation can produce strong Kazakh conversational performance without the resources available for English [11]. The ISSAI KazLLM artifact used here is a quantized release intended for local inference [10]. This project compares it with three general-purpose model families while recording the exact file digest and runtime template.

The selected journal has recently published closely related work on a task-specific Vietnamese summarization model [26], a Tibetan large language model [27] and a fine-grained Chinese mathematical evaluation benchmark [28]. Together these articles show that the venue accepts resource, model and benchmark contributions for Asian languages. The present study differs by emphasizing controlled local inference, error-event annotation and paired statistical comparison for Kazakh rather than model training or task accuracy alone.

Model evaluation in a low-resource language also raises a measurement problem. Automatic overlap metrics reward similarity to a reference wording, yet a practical explanation may be correct in many forms and a fluent answer may still invent a local rule. Purpose-designed reference cards are therefore more suitable here than a single gold response: they state required propositions, acceptable variants and prohibited unsupported specifics while leaving surface realization open. This approach increases annotation effort, but it makes semantic judgments auditable and avoids treating harmless paraphrase as an error.

Quantization and local serving create additional sources of variation that are easy to omit from a paper. Two artifacts with the same parameter count can differ in quantizer, chat template, stop handling and runtime defaults. Even a mutable tag can point to different content over time. The present comparison does not attempt to decompose these factors causally. Instead, it treats each complete artifact-plus-template configuration as the experimental condition and records enough metadata for another machine to reconstruct that condition. This choice favors ecological reproducibility over an architectural ablation.

Error analysis requires a unit that annotators can apply consistently. Traditional machine-translation metrics such as BLEU summarize output quality but do not localize the linguistic mechanism of an error [19]. The present rubric therefore uses four primary categories relevant to Kazakh generation. Grammatical events cover morphology and syntax. Lexical events cover unsuitable word choice when the proposition remains recoverable. Semantic events cover contradictions with the prompt or verified reference card. Code-switching covers unrequested foreign-language spans after explicit exemptions. Surface spelling and punctuation remain secondary because the primary hypothesis concerns errors that change structure, choice, meaning or language.

Reliable human annotation needs more than a written label list [1]. Cohen's kappa measures nominal agreement beyond chance [3], while Krippendorff's alpha supports broader measurement levels and missing observations [12]. Span annotations also require overlap-aware comparison because two annotators may identify the same defect with slightly different boundaries. The protocol therefore uses calibration on development responses, qualification thresholds, independent full annotation, immutable originals and adjudication with written rationales. Agreement is reported before adjudication even if it is weak.

The statistical design follows the paired structure of the experiment. Every prompt forms a block observed under all four models. Friedman's rank test is appropriate for repeated nonparametric comparisons [5, 7], but the project uses a permutation version to preserve the planned finite-sample interpretation. Pairwise signed-rank comparisons follow Wilcoxon [24] and Pratt's zero-retaining variant [20], while Holm's procedure controls family-wise error across six comparisons [9]. Whole-prompt bootstrap resampling preserves the cluster of four model responses generated from one prompt and supports intervals for mean paired differences and detector F1 contrasts [6].
""")
    add_table(doc, ["Study", "Language / scope", "Evidence", "Gap retained here"], [
        ["Maxutov et al. [14]", "Kazakh; seven models", "Pilot model comparison", "No frozen event-level paired protocol"],
        ["KazMMLU [23]", "Kazakh/Russian; regional knowledge", "Multiple-choice benchmark", "Does not localize generation errors"],
        ["Sherkala-Chat [11]", "Kazakh conversational model", "Model/data construction", "Not a four-artifact local error comparison"],
        ["This study", "Kazakh practical generation", "60 prompts, 240 paired responses, two raters", "Limited to exact local quantized artifacts"],
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
Yerkebulan Rakhymbay and Iliyas Aitzhan independently annotate every test response in separately shuffled workbooks. They see the prompt, response and frozen card but not the model identity, timing information, the other rater's labels or detector candidates. Aldiyar Zhaksylyk coordinates files and later adjudicates disagreements while model labels remain hidden. The private model key opens only after the gold file is frozen.

An error event is the smallest continuous fragment requiring one independent correction. Annotators record the exact fragment, zero-based half-open character offsets, inclusive token indices, proposed correction, rationale and any source used. Overlap priority is code-switching, semantic, grammatical and lexical. Repeated occurrences at different locations count separately. Spelling, punctuation, capitalization and spacing are surface events and do not increase the primary rate.

Response-level fields capture refusal, off-task content, missing requirements, repetition and fabricated specificity. Word count, length compliance and truncation come from raw text and Ollama receipts rather than subjective judgment. Calibration uses 12 development responses for training and 20 different responses for blinded qualification. The planned thresholds are at least 80 percent category-presence agreement, Cohen's kappa of at least 0.60 where defined, interval Krippendorff alpha of at least 0.67 for total primary counts and span-match F1 of at least 0.60. A failed threshold requires rubric revision and qualification on unused development material.

The workbook design separates observation from interpretation. Each rater receives a different response order and a stable anonymous identifier. Model names, timings, detector outputs and the other rater's decisions are excluded. Required fields and data validation reduce accidental schema drift, while immutable originals allow agreement to be computed before adjudication. The merge stage identifies disagreements without revealing the model key; the adjudicator must record a decision and rationale rather than silently choosing one file. These controls do not eliminate subjective judgment, but they make each judgment traceable and protect the detector evaluation from label leakage.
""")

    doc.add_heading("3.5 Statistical analysis", level=2)
    add_body(doc, """
For each non-empty response, the primary endpoint equals 100 multiplied by the adjudicated count of grammatical, lexical, semantic and code-switching events divided by word tokens. A zero-word response has an undefined rate and is reported as a generation failure. The primary Friedman analysis uses only prompt blocks with defined rates for all four models. Truncated outputs remain in the main analysis and are excluded only in a sensitivity analysis.

H1 uses a tie-corrected Friedman statistic with 99,999 within-prompt label permutations and seed 2417. Kendall's W reports the omnibus effect size. Six two-sided pairwise Pratt signed-rank permutation tests receive Holm adjustment. For each pair the report includes rank-biserial correlation and the mean response-rate difference with a 95 percent interval from 10,000 whole-prompt bootstrap resamples stratified by task type.

H2 receives support only if H1 is significant, the Holm-adjusted KazLLM-Llama comparison is significant, the KazLLM minus Llama point estimate is negative and its bootstrap interval lies entirely below zero. Failure to satisfy these conditions means the study does not support H2. It does not establish equivalence.

H3 pools adjudicated events and word tokens across Qwen, Llama and Gemma. Category rates are reported per 100 words with prompt-bootstrap intervals. H4 defines a gold code-switching positive as any response with at least one adjudicated code-switching event. The Latin baseline detects a non-exempt word token containing a Latin letter. The fastText component follows efficient text-classification practice [16], testing sentences and sliding three-word windows at confidence 0.85; the hybrid prediction is the union of Latin and fastText positives. Precision, recall and F1 use all 240 responses, with a whole-prompt bootstrap interval for hybrid minus Latin F1.

Pre-specified sensitivity analyses protect the interpretation from avoidable analytic flexibility. The first excludes truncated responses while keeping the same prompt-block rule. The second reports unnormalized primary-event counts alongside rates so a length-driven reversal is visible. The third separates educational and public-information prompts descriptively without promoting subgroup comparisons to new confirmatory hypotheses. Zero-word outputs are accounted for as generation failures rather than assigned an arbitrary infinite or zero rate. Missing blocks, permutation seeds, resample counts and every exclusion are reported in generated metadata so a reader can reconstruct the exact analysis population.
""")

    doc.add_heading("4 Executed readiness evidence", level=1)
    add_body(doc, """
The current repository demonstrates technical readiness rather than a model ranking. Sixteen automated tests pass. They cover prompt validation, stable request construction, receipt reuse, ambiguous-request blocking, workbook blinding, detector behavior, binary metrics, clustered F1 resampling, Friedman components, permutation behavior, Pratt comparisons, Holm adjustment and bootstrap differences. The 60 test prompts pass the exact balance matrix and no development prompt crosses the configured similarity threshold.

All four required models pass an Ollama preflight that checks installation, digest availability and Q4_K_M quantization. One retained development smoke response exists for each model under the intended generation controls. Llama reached the 768-token boundary and repeated content; the run preserves this failure instead of regenerating it. KazLLM returned 109 words with a normal stop. A two-request Qwen check produced identical response SHA-256 values. These observations confirm that the local stack executes the planned requests and retains undesirable outputs.

The repository also captures the Mac hardware summary, operating environment, Python lock file, Ollama version, external language-identification resource hashes and the pinned Universal Dependencies Kazakh treebank resource. Secret scans exclude access tokens, private blinding keys, model binaries and local virtual environments. The test collector remains locked because the 60 reference cards and three team signoffs have not yet been frozen. This lock is an intended safeguard, not a software failure.
""")

    doc.add_heading("5 Results reporting contract", level=1)
    add_body(doc, """
The final Results section will begin with an accounting table for 240 planned requests. It will distinguish completed responses, explicit generation failures, ambiguous timeouts and truncated completions. A second table will report pre-adjudication agreement for response flags, category presence, primary counts and spans. The main model table will show the number of defined prompt blocks, median and mean primary-error rates, bootstrap intervals, mean word counts and failure flags.

The result package will also contain a prompt-level paired visualization rather than only model averages. Each prompt contributes four connected observations so readers can see whether an omnibus difference is broad or driven by a small set of difficult items. A category figure will separate grammatical, lexical, semantic and code-switching rates with whole-prompt intervals. Detector results will appear in a confusion-matrix table with precision, recall and F1 for the Latin baseline and hybrid method. Captions will state the analysis population, denominator, interval method and whether a panel is confirmatory or exploratory.

The omnibus paragraph will report the permutation count, Friedman statistic, p-value and Kendall's W. Pairwise comparisons will appear only with raw and Holm-adjusted p-values, signed effect direction, rank-biserial correlation and bootstrap intervals. H2 will follow its conjunctive decision rule. H3 and H4 will retain exploratory labels in the abstract, Results, Discussion and slides.

No inferential value appears in this document because the independent labels do not yet exist. Substituting model-generated labels or inferred counts would violate the study design and create false agreement. Once both raters submit their original files, the analysis scripts can populate the contracted tables without hand-copying numbers. The manuscript and defense deck must then pass a numerical consistency audit against the generated files.

Results will be interpreted by decision rules rather than by isolated p-values. H1 is supported only by the pre-specified omnibus procedure. H2 additionally requires the KazLLM–Llama contrast, direction and interval conditions. A non-significant comparison is reported as insufficient evidence, not proof of equivalence. H3 and H4 remain exploratory regardless of how favorable their estimates appear. Error examples may illustrate an adjudicated pattern, but they cannot substitute for the aggregated rate or be selected solely because they make one model look unusually good or bad.
""")

    doc.add_heading("6 Discussion", level=1)
    add_body(doc, """
The design favors traceability over breadth. One local machine, one quantized artifact per family and deterministic decoding make the run easier to audit, but the resulting comparison cannot isolate architecture, training data, parameter count, prompt template and quantization as separate causes. Gemma has approximately 12 billion parameters while the other artifacts have about 8 billion. KazLLM and Llama share a family but differ in adaptation and packaging. A lower observed error rate would describe the complete configuration, not prove that one training decision caused the difference.

Purposeful prompts support error discovery but do not form a probability sample of Kazakh language use. Educational and public-information tasks were chosen because errors in these settings are interpretable and consequential. The rates should not be generalized to literature, informal messaging, professional translation or long-form reasoning. The single response per model-prompt pair also estimates performance under the frozen deterministic condition, not variability across sampling temperatures or seeds.

The design also separates repeatability from generality. Temperature zero and a fixed seed reduce one source of run-to-run variation, and the determinism check verifies behavior for a retained sample. They do not prove that every backend, operating-system version or accelerator will emit identical bytes, nor do they estimate a distribution over creative generations. The resulting claims concern the frozen Mac/Ollama environment. Replication on another platform would be valuable, but it should be reported as a new environment rather than mixed silently into the primary run.

Human annotation introduces judgment. Reference cards narrow semantic decisions, calibration exposes ambiguous rules and adjudication produces a usable gold file, yet agreement statistics may still be modest. Reporting agreement before adjudication is therefore essential. Blinding also has limits because raters may recognize stylistic patterns, and a whole foreign-language response can reveal model tendencies. The protocol prevents direct model labels and timing information from appearing in workbooks but cannot guarantee perfect perceptual blinding.

Automatic code-switching detection is deliberately secondary. A Latin script rule can detect English fragments but misses Russian in Cyrillic and can flag identifiers or accepted borrowings. fastText can capture broader language shifts but may misclassify short Kazakh windows. The hybrid detector is evaluated against human gold rather than used to create that gold. Detector candidates remain hidden until independent annotation and adjudication are frozen.

If the study finds model differences, the practical implication is not that one family is universally better. A lower event rate under these controls would identify a stronger tested configuration for short Kazakh educational and public-information responses. The error-category profile can still be useful when total rates are similar: developers may target morphology, lexical choice, factual grounding or language separation differently. Conversely, weak agreement would limit confidence in fine-grained category claims even if total counts can be adjudicated. Reporting both performance and measurement reliability is therefore essential.

The study evaluates locally generated text and does not intentionally collect external participant data or personal information. The annotators are the authors. The supplied materials contain no evidence of formal ethics approval or exemption, so the paper must not invent an approval number. The team should confirm institutional requirements with the instructor and record the resulting determination before external submission.

The intended venue is ACM Transactions on Asian and Low-Resource Language Information Processing because the paper directly evaluates an Asian low-resource language and emphasizes practical language processing. Language Resources and Evaluation is a defensible backup when the paper foregrounds the released prompt resource, annotation protocol and gold spans. Journal choice does not alter the evidence layer, generated tables or limitations.
""")

    doc.add_heading("7 Conclusion", level=1)
    add_body(doc, """
This project replaces inconsistent assignment-stage documents with one reproducible study. The prompt matrix, exact model artifacts, local environment, collection safeguards, annotation instrument and confirmatory analysis are implemented and tested. The official gated KazLLM artifact has been authenticated, hashed, imported and smoke-tested beside the three general-purpose models. The remaining work is irreducibly human: verify the reference cards, sign the frozen bundle, collect the 240 responses, complete two independent annotations and adjudicate disagreements. Only then can the project state which model has the lowest linguistic error rate. Preserving that boundary is part of the result because it prevents an attractive but unsupported final claim.

After the primary study is frozen, future work can replicate the protocol on additional hardware, larger or differently quantized artifacts, and naturally sampled Kazakh requests. Those extensions should retain the same provenance and annotation safeguards while treating every changed model, prompt population or runtime as a new experimental condition. The immediate goal remains narrower: complete one defensible comparison whose evidence can be inspected from prompt to claim.
""")

    doc.add_heading("Declarations", level=1)
    doc.add_heading("Data and code availability", level=2)
    add_body(doc, """
The accompanying version-controlled course repository contains the prompt sets, reference-card templates, frozen protocol, model-artifact manifest, environment capture, collection and analysis code, tests, annotation instruments and document builders. Project-authored code is released under the MIT License; original prompts, protocols and documentation are released under CC BY 4.0. Third-party resources and model artifacts retain their original terms. The gated KazLLM binary and other model weights are not redistributed. Test receipts, original rater files, adjudicated labels and generated result tables will enter the public release only after collection, independent annotation and the three-author freeze are complete.
""")
    doc.add_heading("CRediT author contributions", level=2)
    add_body(doc, """
Aldiyar Zhaksylyk: conceptualization, methodology, software, investigation, data curation, reproducibility, project administration and blinded adjudication. Yerkebulan Rakhymbay: validation, formal analysis, statistical interpretation and independent annotation as Rater 1. Iliyas Aitzhan: independent annotation as Rater 2, writing-review and editing, manuscript integration, visualization review and numerical consistency. All authors are required to review and approve the frozen release before submission.
""")
    doc.add_heading("AI-use declaration", level=2)
    add_body(doc, """
OpenAI Codex assisted with software scaffolding, document drafting, formatting and quality checks. The human authors remain responsible for the study design, source verification, prompt and reference-card content, model execution, both independent annotations, adjudication, statistical interpretation and every submitted claim. No AI-generated annotation is represented as an independent human rating, and no model-generated value is reported as an observed result. AI tools are not authors.
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
    core.comments = "Prepared for SE-2417 course defense. Final linguistic results require frozen human annotations."

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    words = sum(len(re.findall(r"\b[\w'-]+\b", p.text)) for p in doc.paragraphs)
    print(f"{OUT}\nword_count={words}\nparagraphs={len(doc.paragraphs)}")


if __name__ == "__main__":
    main()
