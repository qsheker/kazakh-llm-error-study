# Kazakh LLM Error Study

[![CI](https://github.com/qsheker/kazakh-llm-error-study/actions/workflows/ci.yml/badge.svg)](https://github.com/qsheker/kazakh-llm-error-study/actions/workflows/ci.yml)

Reproducible local comparison of four Q4_K_M language-model configurations on 60 Kazakh prompts (30 educational and 30 public-information prompts).

## Current status

This repository is a clean rebuild. It does **not** claim to recover the historical repository or the missing 60-response pilot receipts described in earlier assignments.

- Protocol v2.1: frozen for the instructor-authorized joint AI-assisted workflow;
  the freeze binds the prompt set, reference cards, analysis plan, annotation
  protocol, model artifacts, exemptions, and coordinator authorization record.
- Test prompts: 60/60 drafted and machine-validated. All 60 reference and
  constraint cards now contain review-ready anchors, exclusions, and
  authoritative sources and are bound into the freeze manifest.
- Public models: installed and smoke-tested on the study Mac; exact Ollama
  digests and template hashes are recorded in `config/model_artifacts.json`.
- KazLLM: authenticated official Q4_K_M artifact imported and smoke-tested;
  source SHA-256 and Ollama metadata are frozen in the repository.
- Dev calibration: 80/80 locally generated responses are retained and pass
  request-accounting validation. The four completed team-assisted calibration
  workbooks are schema/rubric evidence, not independent-rater evidence.
- Engineering verification: 33 tests, Ruff 0.17.5 via `uvx`, syntax
  compilation, `git diff --check`, protocol validation, and the four-model
  macOS preflight pass; public GitHub CI is green.
- Final 240 test responses: complete and validated under the frozen protocol;
  one pre-generation Ollama runner-load failure has preserved incident evidence
  and an identical-payload infrastructure retry.
- Joint-team gold labels: the blinded workbook and balanced 80/80/80 assignment
  exist. A 22-response Qwen QC sample is preserved with hashes but was not
  applied to the workbook; the 240 human reviews remain pending.
- Confirmatory results: unavailable until the reviewed team gold set is
  complete.
- Submission artifacts: an integrated manuscript, an official-template ACM
  submission copy, draft cover letter,
  10-slide defense PDF, journal-fit statement and criteria matrix are built and
  visually checked. They deliberately contain no invented inferential result.

Read `docs/EXECUTION_STATUS.md` for the exact completed/blocked boundary. The
repository deliberately fails closed: it cannot collect the test set unless the
prompt cards, protocol documents, authorization record, model-artifact manifest,
and freeze manifest all agree.

Historical assignments are retained under `docs/archive/` as provenance, not as executable evidence for the final results.

For the exact submit-now package, the remaining sequence and the three-person
defense rehearsal, use `docs/FINAL_SUBMISSION_AND_DEFENSE_RU.md` as the single
operational guide. The supplied Agile “Team Project 2” document belongs to a
different assignment and is not part of this research submission.

Canonical repository: <https://github.com/qsheker/kazakh-llm-error-study>

## Submission artifacts

- `deliverables/Kazakh_LLM_Study_Manuscript.docx` — integrated ACM-style
  manuscript with declarations and appendices.
- `deliverables/Kazakh_LLM_Study_ACM_Submission.docx` — the same controlled
  manuscript transferred into the official one-column ACM Word style set.
- `deliverables/Cover_Letter_TALLIP.docx` — one-page result-bearing cover
  letter; journal submission remains gated by the external evidence checks.
- `deliverables/Final_Submission_and_Defense_Guide_RU.docx` — Russian
  operational handoff for submission, remaining work and defense rehearsal.
- `output/pdf/Kazakh_LLM_Defense_Deck.pdf` — 10-slide defense deck.
- `deliverables/Kazakh_LLM_Defense_Deck.pptx` — editable copy of the same
  result-bearing defense deck.
- `output/packages/Kazakh_LLM_Final_Course_Submission.zip` — ready-to-send
  course package with a hash manifest; it is explicitly not a journal release.
- `docs/JOURNAL_FIT_STATEMENT.md` — completed primary/backup journal record.
- `docs/CRITERIA_MATRIX.md` — criterion-by-criterion status and evidence map.
- `docs/FINAL_SUBMISSION_AND_DEFENSE_RU.md` — single Russian submission and
  defense guide with the exact current gates.
- `annotations/calibration/dev_calibration_v2/` — four blinded calibration
  workbooks plus public integrity manifests; the private model key is excluded
  from Git.

Rebuild the two Word artifacts with:

```bash
.venv/bin/python scripts/build_manuscript.py
.venv/bin/python scripts/build_cover_letter.py
.venv/bin/python scripts/build_final_guide.py
```

Rebuild the official-template copy without overwriting the working manuscript:

```bash
.venv/bin/python scripts/fetch_acm_template.py tmp/acm_submission_template.docx
.venv/bin/python scripts/build_acm_manuscript.py \
  --source deliverables/Kazakh_LLM_Study_Manuscript.docx \
  --template tmp/acm_submission_template.docx \
  --output deliverables/Kazakh_LLM_Study_ACM_Submission.docx
```

Rebuild the editable result-bearing deck and its canonical PDF with the bundled
presentation runtime, then visually inspect every exported slide:

```bash
/Users/qsheker/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node \
  scripts/build_defense_deck.mjs
.venv/bin/python scripts/build_defense_pdf.py \
  --slides-dir .deck-build/slides \
  --output output/pdf/Kazakh_LLM_Defense_Deck.pdf
```

The deck builder reads the frozen analysis outputs and validates the editable
PPTX package before writing it. `build_defense_pdf.py` packages exactly ten
exported slide PNGs and refuses any other sequence.

## Team and accountable work

| Person | Primary accountable work |
|---|---|
| Aldiyar Zhaksylyk | Mac model setup, collection, repository, receipts, reproducibility, protocol and final audit |
| Yerkebulan Rakhymbay | Automated tests, label quality control, statistics, interpretation and validation defense |
| Iliyas Aitzhan | Gold-label/results integration, numerical consistency, visualization, journal fit and final QA |

All contributions must be supported by commits, signed review records, annotation files, execution receipts, or documented reviews. The three-person team has instructor approval even though the supplied general criterion states a maximum of two; the team should retain written evidence of that exception if available.

The operational Russian handoff for the three owners is in
`docs/TEAM_HANDOFF_RU.md`; the exact final submission contents and remaining
gates are in `docs/SUBMISSION_PACKAGE_RU.md`.

## Tested configurations

The protocol identifies artifacts by Ollama content digest and template hash, not by mutable tag alone.

1. `qwen3:8b` — official Ollama Q4_K_M
2. `llama3.1:8b` — official Ollama Q4_K_M
3. `gemma3:12b` — official Ollama Q4_K_M
4. `kazllm:8b-q4_k_m` — local Ollama import of the official gated ISSAI `LLama-3.1-KazLLM-1.0-8B-GGUF4` Q4_K_M file

Generation uses a fresh one-message conversation for every model/prompt pair. The exact controls are in `config/protocol.json`; both generation and request-order seeds are 2417.

## macOS setup

The audited machine is an Apple M4 MacBook Air with 24 GB unified memory. Its pre-existing Homebrew Python 3.14 and a freshly installed Homebrew Python 3.12 both fail `platform.mac_ver()`/`ensurepip` on the current macOS build, so the verified setup uses the already installed `uv` tool to provision an isolated CPython 3.12:

```bash
uv python install 3.12
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e '.[dev]'
```

Start Ollama in a separate terminal and install the three public artifacts:

```bash
ollama serve
ollama pull qwen3:8b
ollama pull llama3.1:8b
ollama pull gemma3:12b
```

KazLLM is intentionally not replaced with an unofficial artifact. The study Mac
downloaded the named GGUF from the pinned official Hugging Face revision,
verified and froze its SHA-256, and imported it with the procedure documented in
`docs/kazllm_import.md`.

## Validation and collection

Machine-check the prompt matrix and dev leakage:

```bash
.venv/bin/python scripts/validate_protocol.py
```

Inspect a collection plan without inference:

```bash
.venv/bin/python scripts/collect.py --dataset dev
```

Verify that all four exact artifacts are installed:

```bash
.venv/bin/python scripts/collect.py --dataset dev --preflight
.venv/bin/python scripts/capture_model_artifacts.py
```

Run a dev collection only after preflight:

```bash
.venv/bin/python scripts/collect.py --dataset dev --send --run-id dev_v2
```

Test collection is programmatically locked unless `config/protocol.json` and
`protocol/freeze_manifest.json` both carry the joint AI-assisted frozen status
and every frozen hash still matches. The authorization record truthfully states
that permission was reported by the coordinator and that no written instructor
letter or another person's signature was fabricated.

## Evidence and recovery rules

- Every request writes an `.inflight` marker before contacting Ollama.
- A completed receipt is reused only when its saved request exactly matches.
- An ambiguous timeout blocks automatic retry; deleting the marker merely to obtain a cleaner answer is prohibited.
- Poor, short, repetitive, refused, off-task, and truncated responses are retained.
- The model snapshot is compared before and after collection.
- Raw responses are immutable inputs; normalization and tokenization create derived copies.
- No human label may be inferred from detector output.

## Joint AI-assisted annotation boundary

The final labels are one joint-team gold set, not two independent ratings. AI
may draft labels and run consistency checks, while model identity and detector
candidates remain hidden. The final analysis unlocks only after all 240 blind
IDs have resolved labels and a review-log row naming the responsible team member.
The workbook builder assigns 80 pending blind IDs to each team member so the
response-review workload starts evenly balanced; an assignment is not treated
as a completed review.
Kappa, alpha, and span-F1 values from duplicated team files are not reported as
human reliability evidence.

The evidence pipeline is explicit:

```bash
.venv/bin/python scripts/validate_run.py runs/final_test_v2 --expected 240
.venv/bin/python scripts/validate_annotation_workbook.py annotations/team_gold/final_test_v2__team_gold.xlsx --expected-responses 240
.venv/bin/python scripts/analyze_final.py
```

`scripts/draft_team_annotations.py` is an optional, resumable helper. Its
current provenance records a 22-response quality-control sample that was not
applied to the workbook or review log.

Validation and team review remain blinded. The final analysis opens the private
model mapping only after the team gold workbook and review log are frozen.

## Reproducing results

The 240 receipts, reviewed team labels, generated tables and result-bearing manuscript now exist. Their hashes are recorded in `results/derived/final_test_v2/input_hashes.json`. The release tag `final` must still not be created before every external-evidence and clean-release check in `docs/RELEASE_CHECKLIST.md` passes.

The machine-enforced release audit is:

```bash
.venv/bin/python scripts/release_gate.py
```

It exits nonzero and names every missing evidence item until the protocol,
receipts, reviewed team gold, final analysis, institutional
records, outside reproduction, public remote, and clean worktree all exist.

## Ethics and data statement

The study evaluates locally generated text and does not intentionally collect external participant data or personal information. The three annotators are the authors. No formal ethics approval or exemption has been evidenced in the supplied materials; the manuscript must state this accurately and the team must confirm institutional requirements with the instructor before submission.

## Licences

Project software is MIT-licensed. Project-authored prompts, protocols and
documentation are CC BY 4.0. Third-party resources, archived coursework and
model artifacts retain their original terms; see `DATA_LICENSE.md` and
`resources/PROVENANCE.md`.
