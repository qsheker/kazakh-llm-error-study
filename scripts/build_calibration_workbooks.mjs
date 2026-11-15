#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const [bundlePath, outputDir] = process.argv.slice(2);
if (!bundlePath || !outputDir) {
  throw new Error("usage: build_calibration_workbooks.mjs BUNDLE_JSON OUTPUT_DIR");
}

const bundle = JSON.parse(await fs.readFile(bundlePath, "utf8"));
const phases = ["training", "qualification"];
const raters = ["rater_1", "rater_2"];
const fontFamily = "Arial";
const responseHeaders = [
  "blind_id",
  "prompt_id",
  "task_type",
  "prompt_text",
  "response_text",
  "reference_or_constraint_card",
  "word_count_read_only",
  "finish_reason_read_only",
  "refusal",
  "off_task",
  "requirement_missing",
  "missing_requirements",
  "repetition",
  "fabricated_specificity",
  "rater_comments",
];
const eventHeaders = [
  "blind_id",
  "event_id",
  "category",
  "exact_fragment",
  "start_offset_zero_based",
  "end_offset_exclusive",
  "start_token_one_based",
  "end_token_one_based",
  "proposed_correction",
  "rationale",
  "source",
  "needs_adjudication",
];

function sha256(bytes) {
  return crypto.createHash("sha256").update(bytes).digest("hex");
}

function styleHeader(range) {
  range.format = {
    fill: "#17324D",
    font: { name: fontFamily, size: 10, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "inside", style: "thin", color: "#FFFFFF" },
  };
  range.format.rowHeight = 30;
}

function styleBody(range) {
  range.format.font = { name: fontFamily, size: 10, color: "#17202A" };
  range.format.verticalAlignment = "top";
  range.format.wrapText = true;
}

function createWorkbook(records, phase, rater) {
  const workbook = Workbook.create();
  const responses = workbook.worksheets.add("Responses");
  const events = workbook.worksheets.add("Error events");
  const instructions = workbook.worksheets.add("Instructions");
  responses.showGridLines = false;
  events.showGridLines = false;
  instructions.showGridLines = false;
  responses.tabColor = "#17324D";
  events.tabColor = "#476D8C";
  instructions.tabColor = "#819CB3";

  const responseRows = records.map((record) => [
    record.blind_id,
    record.prompt_id,
    record.task_type,
    record.prompt_text,
    record.response_text,
    record.reference_or_constraint_card,
    record.word_count_read_only,
    record.finish_reason_read_only,
    "",
    "",
    "",
    "",
    "",
    "",
    "",
  ]);
  responses.getRangeByIndexes(0, 0, responseRows.length + 1, responseHeaders.length).values = [
    responseHeaders,
    ...responseRows,
  ];
  styleHeader(responses.getRange(`A1:O1`));
  styleBody(responses.getRange(`A2:O${responseRows.length + 1}`));
  responses.freezePanes.freezeRows(1);
  responses.freezePanes.freezeColumns(3);
  responses.getRange(`I2:K${responseRows.length + 1}`).dataValidation = {
    rule: { type: "list", values: ["yes", "no", "needs_adjudication"] },
  };
  responses.getRange(`M2:N${responseRows.length + 1}`).dataValidation = {
    rule: { type: "list", values: ["yes", "no", "needs_adjudication"] },
  };
  const responseWidths = [22, 10, 14, 48, 68, 58, 14, 17, 16, 16, 20, 34, 16, 22, 34];
  responseWidths.forEach((width, index) => {
    responses.getRangeByIndexes(0, index, responseRows.length + 1, 1).format.columnWidth = width;
  });
  responses.getRange(`A2:O${responseRows.length + 1}`).format.rowHeight = 105;
  responses.getRange(`G2:G${responseRows.length + 1}`).format.numberFormat = "0";

  const blankEventRows = Math.max(200, records.length * 10);
  events.getRangeByIndexes(0, 0, blankEventRows + 1, eventHeaders.length).values = [
    eventHeaders,
    ...Array.from({ length: blankEventRows }, () => Array(eventHeaders.length).fill("")),
  ];
  styleHeader(events.getRange("A1:L1"));
  styleBody(events.getRange(`A2:L${blankEventRows + 1}`));
  events.freezePanes.freezeRows(1);
  events.freezePanes.freezeColumns(2);
  events.getRange(`C2:C${blankEventRows + 1}`).dataValidation = {
    rule: {
      type: "list",
      values: ["grammatical", "lexical", "semantic", "code_switching", "surface"],
    },
  };
  events.getRange(`L2:L${blankEventRows + 1}`).dataValidation = {
    rule: { type: "list", values: ["yes", "no"] },
  };
  const eventWidths = [22, 16, 20, 42, 19, 19, 18, 18, 42, 52, 42, 20];
  eventWidths.forEach((width, index) => {
    events.getRangeByIndexes(0, index, blankEventRows + 1, 1).format.columnWidth = width;
  });
  events.getRange(`A2:L${blankEventRows + 1}`).format.rowHeight = 36;
  events.getRange(`E2:H${blankEventRows + 1}`).format.numberFormat = "0";

  const qualificationRule =
    phase === "qualification"
      ? "Pass only if category-presence agreement is at least 80%, Cohen kappa is at least 0.60 where defined, interval alpha for primary counts is at least 0.67, and exact span F1 is at least 0.60."
      : "After both raters finish, discuss disagreements and clarify the rubric. Training rows never enter qualification or final analysis.";
  const instructionRows = [
    ["Workbook", `${phase} / ${rater}`],
    ["Independence", "Complete this workbook without viewing another rater's workbook, model identities, or detector output."],
    ["Response flags", "Fill refusal, off_task, requirement_missing, repetition, and fabricated_specificity for every response."],
    ["Missing requirements", "When requirement_missing is yes, identify the omitted prompt or card requirement."],
    ["Error event", "Use the smallest continuous fragment requiring one independent correction."],
    ["Offsets", "Use zero-based character offsets; end_offset_exclusive is the first character after the fragment."],
    ["Tokens", "Use one-based inclusive token positions based on visible whitespace-delimited tokens."],
    ["Priority", "For one overlapping interpretation use code_switching, then semantic, grammatical, lexical."],
    ["Surface", "Spelling, punctuation, capitalization, and spacing use surface and do not enter the primary endpoint."],
    ["Uncertainty", "Use needs_adjudication instead of forcing certainty."],
    ["Do not rename", "Do not rename worksheets or columns and do not overwrite read-only fields."],
    ["Phase rule", qualificationRule],
  ];
  instructions.getRangeByIndexes(0, 0, instructionRows.length + 1, 2).values = [
    ["Rule", "Required behavior"],
    ...instructionRows,
  ];
  styleHeader(instructions.getRange("A1:B1"));
  styleBody(instructions.getRange(`A2:B${instructionRows.length + 1}`));
  instructions.getRange("A1:A20").format.columnWidth = 24;
  instructions.getRange("B1:B20").format.columnWidth = 105;
  instructions.getRange(`A2:B${instructionRows.length + 1}`).format.rowHeight = 44;
  instructions.freezePanes.freezeRows(1);

  return workbook;
}

const qaDir = path.join("results", "tmp", "calibration_previews", bundle.run_id);
const plannedPaths = [
  ...phases.flatMap((phase) =>
    raters.map((rater) =>
      path.join(outputDir, rater, `${bundle.run_id}__${phase}__${rater}.xlsx`),
    ),
  ),
  ...phases.map((phase) => path.join(outputDir, `${phase}_blinded_manifest.json`)),
  path.join(outputDir, "workbook_manifest.json"),
];
for (const plannedPath of plannedPaths) {
  try {
    await fs.access(plannedPath);
    throw new Error(`refusing to overwrite ${plannedPath}`);
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }
}

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(qaDir, { recursive: true });
const outputs = [];
const blindedManifests = {};
for (const phase of phases) {
  const canonicalRecords = bundle.phases?.[phase]?.rater_1;
  if (!Array.isArray(canonicalRecords)) {
    throw new Error(`${phase}/rater_1 records are missing`);
  }
  const manifestRows = canonicalRecords
    .map((record) => {
      if (sha256(Buffer.from(record.response_text, "utf8")) !== record.response_sha256) {
        throw new Error(`${phase}/${record.blind_id} response hash does not match source receipt`);
      }
      if (sha256(Buffer.from(record.prompt_text, "utf8")) !== record.prompt_text_sha256) {
        throw new Error(`${phase}/${record.blind_id} prompt hash does not match bundle`);
      }
      if (
        sha256(Buffer.from(record.reference_or_constraint_card, "utf8")) !==
        record.reference_card_sha256
      ) {
        throw new Error(`${phase}/${record.blind_id} reference-card hash does not match bundle`);
      }
      return {
        blind_id: record.blind_id,
        prompt_id: record.prompt_id,
        task_type: record.task_type,
        prompt_text_sha256: record.prompt_text_sha256,
        response_text_sha256: record.response_sha256,
        reference_card_sha256: record.reference_card_sha256,
        word_count_read_only: record.word_count_read_only,
        finish_reason_read_only: record.finish_reason_read_only,
      };
    })
    .sort((left, right) => left.blind_id.localeCompare(right.blind_id));
  blindedManifests[phase] = { responses: manifestRows };
  await fs.writeFile(
    path.join(outputDir, `${phase}_blinded_manifest.json`),
    `${JSON.stringify(blindedManifests[phase], null, 2)}\n`,
    "utf8",
  );
  for (const rater of raters) {
    const records = bundle.phases?.[phase]?.[rater];
    const expected = phase === "training" ? 12 : 20;
    if (!Array.isArray(records) || records.length !== expected) {
      throw new Error(`${phase}/${rater} must contain ${expected} records`);
    }
    const blindIds = records.map((record) => record.blind_id).sort();
    const manifestBlindIds = manifestRows.map((record) => record.blind_id).sort();
    if (JSON.stringify(blindIds) !== JSON.stringify(manifestBlindIds)) {
      throw new Error(`${phase}/${rater} blind IDs differ from the integrity manifest`);
    }
    const workbook = createWorkbook(records, phase, rater);
    workbook.recalculate();
    const tableCheck = await workbook.inspect({
      kind: "table",
      range: `Responses!A1:O${Math.min(records.length + 1, 5)}`,
      include: "values,formulas",
      tableMaxRows: 5,
      tableMaxCols: 15,
      maxChars: 8000,
    });
    if (!tableCheck.ndjson.includes("blind_id")) {
      throw new Error(`${phase}/${rater} Responses inspection failed`);
    }
    const errors = await workbook.inspect({
      kind: "match",
      searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
      options: { useRegex: true, maxResults: 50 },
      summary: `${phase}/${rater} formula error scan`,
    });
    if (errors.ndjson.includes('"match"')) {
      throw new Error(`${phase}/${rater} contains a spreadsheet error`);
    }
    for (const sheetName of ["Responses", "Error events", "Instructions"]) {
      const renderRange =
        sheetName === "Responses"
          ? `A1:O${records.length + 1}`
          : sheetName === "Error events"
            ? "A1:L20"
            : "A1:B13";
      const preview = await workbook.render({
        sheetName,
        range: renderRange,
        autoCrop: "all",
        scale: 1,
        format: "png",
      });
      const previewBytes = new Uint8Array(await preview.arrayBuffer());
      await fs.writeFile(path.join(qaDir, `${phase}__${rater}__${sheetName.replaceAll(" ", "_")}.png`), previewBytes);
    }
    const raterDir = path.join(outputDir, rater);
    await fs.mkdir(raterDir, { recursive: true });
    const outputPath = path.join(raterDir, `${bundle.run_id}__${phase}__${rater}.xlsx`);
    const exported = await SpreadsheetFile.exportXlsx(workbook);
    await exported.save(outputPath);
    const bytes = await fs.readFile(outputPath);
    outputs.push({ phase, rater, path: outputPath, bytes: bytes.length, sha256: sha256(bytes) });
  }
}

await fs.writeFile(
  path.join(outputDir, "workbook_manifest.json"),
  `${JSON.stringify({ run_id: bundle.run_id, bundle_sha256: sha256(await fs.readFile(bundlePath)), outputs }, null, 2)}\n`,
  "utf8",
);
console.log(JSON.stringify({ qaDir, outputs }, null, 2));
