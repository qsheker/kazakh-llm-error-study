#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const RESULT_DIR = path.join(ROOT, "results", "derived", "final_test_v2");
const BUILD_DIR = path.join(ROOT, ".deck-build");
const SLIDE_DIR = path.join(BUILD_DIR, "slides");
const CANDIDATE = path.join(BUILD_DIR, "candidate.pptx");
const VALIDATION_RECEIPT = path.join(BUILD_DIR, "validation.json");
const FINAL = path.join(ROOT, "deliverables", "Kazakh_LLM_Defense_Deck.pptx");
const SKILL_DIR = "/Users/qsheker/.codex/plugins/cache/openai-primary-runtime/presentations/26.1112.11011/skills/presentations";
const RUNTIME_PYTHON = "/Users/qsheker/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3";
const RUNTIME_NODE_MODULES = "/Users/qsheker/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";
process.env.RUNTIME_NODE_MODULES ??= RUNTIME_NODE_MODULES;
const { Presentation, PresentationFile } = await import(pathToFileURL(
  path.join(RUNTIME_NODE_MODULES, "@oai", "artifact-tool", "dist", "artifact_tool.mjs"),
).href);

const W = 1280;
const H = 720;
const FONT = "Arial";
const BG = "#F4F7F8";
const WHITE = "#FFFFFF";
const NAVY = "#123247";
const TEAL = "#2A88A7";
const GRAY = "#647784";
const LIGHT = "#D6E1E6";
const GREEN = "#247A5A";
const RED = "#A34747";

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

function textbox(slide, text, left, top, width, height, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left, top, width, height },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontFamily: FONT,
    fontSize: options.fontSize ?? 20,
    bold: options.bold ?? false,
    color: options.color ?? NAVY,
    italic: options.italic ?? false,
  };
  return shape;
}

function baseSlide(presentation, number, title, background = BG) {
  const slide = presentation.slides.add();
  slide.background.fill = background;
  textbox(slide, title, 72, 62, 1030, 54, { fontSize: 34, bold: true });
  textbox(slide, String(number).padStart(2, "0"), 1170, 64, 42, 24, {
    fontSize: 14,
    bold: true,
    color: TEAL,
  });
  return slide;
}

function metric(slide, value, label, left, top, width, note = "") {
  textbox(slide, value, left, top, width, 70, { fontSize: 48, bold: true });
  textbox(slide, label, left, top + 74, width, 34, { fontSize: 19, bold: true, color: TEAL });
  if (note) textbox(slide, note, left, top + 120, width, 76, { fontSize: 17, color: GRAY });
}

function dataBars(slide, items, left, top, width, rowHeight, maxValue, digits = 2, accentIndex = -1) {
  const labelWidth = Math.min(180, width * 0.34);
  const valueWidth = 74;
  const barWidth = width - labelWidth - valueWidth - 24;
  items.forEach(([label, value], index) => {
    const rowTop = top + index * rowHeight;
    textbox(slide, label, left, rowTop + 5, labelWidth - 10, 30, {
      fontSize: 16,
      bold: true,
    });
    const track = slide.shapes.add({
      geometry: "rect",
      position: { left: left + labelWidth, top: rowTop + 9, width: barWidth, height: 22 },
      fill: LIGHT,
      line: { style: "solid", fill: "none", width: 0 },
    });
    track.name = `track-${label}`;
    const bar = slide.shapes.add({
      geometry: "rect",
      position: {
        left: left + labelWidth,
        top: rowTop + 9,
        width: Math.max(3, barWidth * (value / maxValue)),
        height: 22,
      },
      fill: index === accentIndex ? GREEN : TEAL,
      line: { style: "solid", fill: "none", width: 0 },
    });
    bar.name = `value-${label}`;
    textbox(slide, value.toFixed(digits), left + labelWidth + barWidth + 12, rowTop + 3, valueWidth, 32, {
      fontSize: 16,
      bold: true,
    });
  });
}

function statusRow(slide, code, statement, status, top) {
  textbox(slide, code, 80, top, 60, 30, { fontSize: 18, bold: true, color: TEAL });
  textbox(slide, statement, 170, top - 2, 760, 50, { fontSize: 19 });
  const supported = status === "SUPPORTED";
  textbox(slide, status, 980, top, 210, 30, {
    fontSize: 16,
    bold: true,
    color: supported ? GREEN : RED,
  });
}

function addNotes(slide, text) {
  slide.speakerNotes.text = text;
}

const summary = JSON.parse(await fs.readFile(path.join(RESULT_DIR, "summary.json"), "utf8"));
const responseCsv = await fs.readFile(path.join(RESULT_DIR, "response_metrics.csv"), "utf8");
const responseLines = responseCsv.trim().split(/\r?\n/);
const headers = responseLines[0].split(",");
const modelIndex = headers.indexOf("model_label");
const truncatedIndex = headers.indexOf("truncated");
const truncationCounts = { qwen3_8b: 0, llama31_8b: 0, gemma3_12b: 0, kazllm_8b: 0 };
for (const line of responseLines.slice(1)) {
  const values = line.split(",");
  if (values[truncatedIndex] === "True") truncationCounts[values[modelIndex]] += 1;
}

const presentation = Presentation.create({ slideSize: { width: W, height: H } });

{
  const slide = presentation.slides.add();
  slide.background.fill = BG;
  textbox(slide, "DEFENSE DECK", 1040, 64, 170, 28, { fontSize: 14, bold: true, color: TEAL });
  textbox(slide, "Evaluating Kazakh Language Errors\nin Local Large Language Models", 72, 120, 980, 150, {
    fontSize: 48,
    bold: true,
  });
  textbox(slide, "Final results from a frozen four-model protocol on 60 Kazakh prompts", 72, 332, 920, 44, {
    fontSize: 22,
    color: GRAY,
  });
  textbox(slide, "Aldiyar Zhaksylyk    Yerkebulan Rakhymbay    Iliyas Aitzhan", 72, 552, 820, 30, {
    fontSize: 18,
    bold: true,
  });
  textbox(slide, "SE-2417    2026", 72, 600, 320, 28, { fontSize: 16, color: GRAY });
  addNotes(slide, "Source: frozen protocol and results/derived/final_test_v2/summary.json.");
}

{
  const slide = baseSlide(presentation, 2, "Research problem", WHITE);
  textbox(slide, "Kazakh remains underrepresented in model training and evaluation", 80, 170, 1050, 48, {
    fontSize: 30,
    bold: true,
  });
  textbox(slide, "Broad benchmarks measure knowledge or task accuracy. They do not show which linguistic failures make educational and public-information responses unreliable.", 80, 252, 1040, 92, {
    fontSize: 21,
    color: GRAY,
  });
  textbox(slide, "This study counts grammatical, lexical, semantic, and code-switching events under one frozen local protocol. Every response stays in the evidence, including truncated or repetitive output.", 80, 400, 1050, 100, {
    fontSize: 22,
    bold: true,
  });
  textbox(slide, "Scope: one quantized artifact per model family, 60 purposeful prompts, and one deterministic response per model and prompt.", 80, 548, 1080, 54, {
    fontSize: 17,
    color: GRAY,
  });
  addNotes(slide, "Source: manuscript Sections 1 and 3; frozen protocol.");
}

{
  const slide = baseSlide(presentation, 3, "Research questions and outcomes");
  statusRow(slide, "H1", "At least one model differs in total primary-error rate per 100 words.", "SUPPORTED", 152);
  statusRow(slide, "H2", "KazLLM has a lower rate than Llama 3.1 8B.", "SUPPORTED", 250);
  statusRow(slide, "H3", "Code-switching is the most frequent category across the general-purpose models.", "NOT SUPPORTED", 348);
  statusRow(slide, "H4", "The hybrid detector has higher F1 than the Latin-script baseline.", "NOT SUPPORTED", 446);
  textbox(slide, "H1 and H2 were confirmatory. H3 and H4 were exploratory.", 80, 584, 900, 34, {
    fontSize: 18,
    bold: true,
    color: GRAY,
  });
  addNotes(slide, "Source: results/derived/final_test_v2/summary.json.");
}

{
  const slide = baseSlide(presentation, 4, "Frozen study design", WHITE);
  metric(slide, "60", "Kazakh prompts", 80, 180, 270, "30 educational\n30 public-information");
  metric(slide, "4", "local Q4_K_M models", 430, 180, 300, "Qwen 3 8B, Llama 3.1 8B\nGemma 3 12B, KazLLM 8B");
  metric(slide, "240", "retained responses", 830, 180, 300, "one fresh conversation\nseed 2417, temperature 0");
  textbox(slide, "All 60 prompt blocks are complete. The collector preserved failed, repetitive, off-task, and truncated outputs. Quality-based regeneration was prohibited.", 80, 500, 1080, 86, {
    fontSize: 21,
    bold: true,
  });
  addNotes(slide, "Source: summary.json design block and immutable request receipts.");
}

{
  const slide = baseSlide(presentation, 5, "Exact local model artifacts");
  const models = [
    ["Qwen 3 8B", "500a1f067a9f", "Q4_K_M, 5.2 GB"],
    ["Llama 3.1 8B", "46e0c10c039e", "Q4_K_M, 4.9 GB"],
    ["Gemma 3 12B", "b92b218582c5", "Q4_K_M, 8.2 GB"],
    ["KazLLM 8B", "2dacc6fb6467", "Q4_K_M, 4.9 GB"],
  ];
  models.forEach(([name, digest, size], index) => {
    const left = 80 + index * 292;
    textbox(slide, name, left, 200, 245, 32, { fontSize: 20, bold: true });
    textbox(slide, digest, left, 258, 245, 28, { fontSize: 17, bold: true, color: TEAL });
    textbox(slide, size, left, 310, 245, 28, { fontSize: 17, color: GRAY });
  });
  textbox(slide, "The repository records content digests, template hashes, parameter hashes, Ollama 0.33.3, and the official KazLLM GGUF SHA-256. Mutable model tags do not define the experiment.", 80, 430, 1080, 90, {
    fontSize: 21,
    bold: true,
  });
  textbox(slide, "Study Mac: Apple M4 MacBook Air, 24 GB unified memory", 80, 570, 800, 30, {
    fontSize: 17,
    color: GRAY,
  });
  addNotes(slide, "Source: evidence/model_manifest.json and evidence/environment.json.");
}

{
  const slide = baseSlide(presentation, 6, "Joint AI-assisted annotation workflow", WHITE);
  const columns = [
    ["AI draft", "Blind suggestions only\nNo model identity\nNo approval authority"],
    ["Yerkebulan", "Test verification\nLabel quality control\nStatistical checks"],
    ["Iliyas", "Gold-label integration\nResults integration\nVisualization checks"],
    ["Aldiyar", "Protocol and collection\nProvenance and repository\nFinal audit"],
  ];
  columns.forEach(([head, body], index) => {
    const left = 80 + index * 292;
    textbox(slide, head, left, 170, 240, 30, { fontSize: 20, bold: true, color: TEAL });
    textbox(slide, body, left, 226, 245, 105, { fontSize: 18, color: GRAY });
  });
  textbox(slide, "240 approved response rows, 855 reviewed events, 80 assigned responses per teammate", 80, 410, 1080, 40, {
    fontSize: 24,
    bold: true,
  });
  textbox(slide, "The coordinator entered approval records after the assigned reviewers confirmed them. The study reports one team-consensus gold set and no independent inter-annotator reliability estimate.", 80, 490, 1080, 86, {
    fontSize: 19,
    color: GRAY,
  });
  addNotes(slide, "Source: annotations/team_gold/team_review_log.csv and the validated final workbook. Approval-entry provenance reflects the team's stated workflow.");
}

{
  const slide = baseSlide(presentation, 7, "Primary error rates by model");
  const modelItems = ["Qwen", "Llama", "Gemma", "KazLLM"].map((name, index) => [
    name,
    summary.models[index].all_defined_mean_response_rate,
  ]);
  textbox(slide, "Mean reviewed events per 100 words", 80, 160, 620, 30, {
    fontSize: 17,
    color: GRAY,
  });
  dataBars(slide, modelItems, 80, 218, 690, 76, 5.5, 2, 3);
  textbox(slide, "H1 supported", 850, 172, 290, 38, { fontSize: 24, bold: true, color: GREEN });
  textbox(slide, "Friedman statistic", 850, 246, 280, 28, { fontSize: 17, color: GRAY });
  textbox(slide, "51.16", 850, 278, 280, 50, { fontSize: 38, bold: true });
  textbox(slide, "p = 0.00001\n99,999 permutations\nKendall's W = 0.284", 850, 350, 310, 120, {
    fontSize: 20,
    color: GRAY,
  });
  textbox(slide, "KazLLM had the lowest mean rate in the frozen comparison.", 850, 520, 330, 68, {
    fontSize: 19,
    bold: true,
  });
  addNotes(slide, "Source: model_rates.csv and summary.json. Error bars are reported in the manuscript table; the slide uses means for legibility.");
}

{
  const slide = baseSlide(presentation, 8, "Confirmatory contrast and retained failures", WHITE);
  textbox(slide, "H2 supported", 80, 160, 300, 38, { fontSize: 24, bold: true, color: GREEN });
  textbox(slide, "KazLLM minus Llama", 80, 226, 360, 34, { fontSize: 19, color: GRAY });
  textbox(slide, "-2.53", 80, 266, 360, 82, { fontSize: 58, bold: true });
  textbox(slide, "events per 100 words", 80, 350, 360, 34, { fontSize: 19, color: GRAY });
  textbox(slide, "95% prompt-bootstrap interval\n-3.94 to -1.14\nHolm-adjusted p = 0.01134", 80, 430, 380, 120, {
    fontSize: 20,
    bold: true,
  });

  textbox(slide, "98 length-truncated responses remained in the primary analysis", 560, 164, 610, 70, {
    fontSize: 26,
    bold: true,
  });
  metric(slide, String(truncationCounts.llama31_8b), "Llama", 570, 280, 150);
  metric(slide, String(truncationCounts.kazllm_8b), "KazLLM", 760, 280, 150);
  metric(slide, String(truncationCounts.qwen3_8b), "Qwen", 950, 280, 150);
  textbox(slide, "Every prompt block contained at least one truncated response. The planned exclude-truncated sensitivity therefore had zero complete blocks and was not estimable.", 560, 470, 590, 108, {
    fontSize: 19,
    color: GRAY,
  });
  addNotes(slide, "Source: summary.json h2 and sensitivity blocks; response_metrics.csv truncation counts. Gemma had 0 truncated responses.");
}

{
  const slide = baseSlide(presentation, 9, "Exploratory findings");
  textbox(slide, "H3 not supported", 80, 144, 430, 34, { fontSize: 22, bold: true, color: RED });
  textbox(slide, "Primary categories across the three general-purpose models", 80, 186, 510, 30, {
    fontSize: 17,
    color: GRAY,
  });
  dataBars(slide, [
    ["Semantic", 1.1962],
    ["Lexical", 1.1453],
    ["Grammatical", 1.0028],
    ["Code-switching", 0.0560],
  ], 80, 252, 500, 66, 1.5, 2);

  textbox(slide, "H4 not supported", 690, 144, 430, 34, { fontSize: 22, bold: true, color: RED });
  textbox(slide, "Response-level code-switching detector F1", 690, 186, 450, 30, {
    fontSize: 17,
    color: GRAY,
  });
  dataBars(slide, [
    ["Latin", 0.0833],
    ["fastText", 0.1481],
    ["Hybrid", 0.1412],
  ], 690, 252, 490, 76, 0.2, 3);
  textbox(slide, "Hybrid minus Latin F1 = 0.058, 95% CI -0.090 to 0.198. The interval crossed zero.", 690, 520, 500, 80, {
    fontSize: 17,
    bold: true,
  });
  addNotes(slide, "Source: summary.json h3 and h4 blocks. Category values are pooled rates per 100 words.");
}

{
  const slide = baseSlide(presentation, 10, "Defense ownership and final takeaway", WHITE);
  const columns = [
    ["Aldiyar", "Local model execution\nCollection and receipts\nProtocol, provenance, final audit"],
    ["Yerkebulan", "Tests and label quality\nStatistical validation\nInterpretation and limitations"],
    ["Iliyas", "Gold and results integration\nNumerical consistency\nVisual and journal-fit checks"],
  ];
  columns.forEach(([head, body], index) => {
    const left = 80 + index * 380;
    textbox(slide, head, left, 160, 320, 32, { fontSize: 21, bold: true, color: TEAL });
    textbox(slide, body, left, 214, 330, 110, { fontSize: 18, color: GRAY });
  });
  textbox(slide, "Final takeaway", 80, 390, 300, 38, { fontSize: 26, bold: true });
  textbox(slide, "Under the frozen local protocol, model error rates differed. KazLLM had the lowest reviewed mean rate and the confirmatory contrast with Llama supported H2. Semantic and lexical errors mattered more than code-switching, and detector gains remained uncertain.", 80, 448, 1080, 124, {
    fontSize: 22,
    bold: true,
  });
  textbox(slide, "Each teammate owns one indispensable evidence chain and must still understand the whole study.", 80, 610, 1050, 34, {
    fontSize: 18,
    color: GRAY,
  });
  addNotes(slide, "Source: final manuscript, defense plan, and generated results. Speaking order: Aldiyar 0:00-3:20; Yerkebulan 3:20-6:40; Iliyas 6:40-10:00.");
}

await fs.mkdir(BUILD_DIR, { recursive: true });
await fs.mkdir(SLIDE_DIR, { recursive: true });
await fs.mkdir(path.dirname(FINAL), { recursive: true });

for (const [index, slide] of presentation.slides.items.entries()) {
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  await writeBlob(path.join(SLIDE_DIR, `slide-${index + 1}.png`), png);
}

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(CANDIDATE);

// The finalizer never overwrites. This builder owns this one canonical output,
// so remove only that exact prior artifact before writing the validated rebuild.
await fs.rm(FINAL, { force: true });
await fs.rm(VALIDATION_RECEIPT, { force: true });

const { finalizePresentation } = await import(pathToFileURL(
  path.join(SKILL_DIR, "container_tools", "artifact_tool_utils.mjs"),
).href);

const requirements = {
  explicitTotalSlideCount: 10,
  requiredNativeTableOwnerSlides: [],
};

await finalizePresentation({
  ...requirements,
  workspaceDir: ROOT,
  candidatePath: CANDIDATE,
  finalPath: FINAL,
  pythonExecutable: RUNTIME_PYTHON,
  integrityValidatorPath: path.join(SKILL_DIR, "container_tools", "inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(SKILL_DIR, "container_tools", "inspect_presentation_layout_geometry.py"),
  layoutArgs: [
    "--expected-slide-size-emu", "12192000,6858000",
    "--validate-heading-fit",
  ],
  requiredNativeTableOwnerSlides: [],
  fontPolicy: { basis: "design", families: [FONT] },
  verifyArtifactToolImport: true,
  receiptPath: VALIDATION_RECEIPT,
});

console.log(FINAL);
console.log(SLIDE_DIR);
