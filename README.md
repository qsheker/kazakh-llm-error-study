# Kazakh LLM Error Study

[![CI](https://github.com/qsheker/kazakh-llm-error-study/actions/workflows/ci.yml/badge.svg)](https://github.com/qsheker/kazakh-llm-error-study/actions/workflows/ci.yml)

Reproducible local comparison of four Q4_K_M language-model configurations on 60 Kazakh prompts (30 educational and 30 public-information prompts).

## Current status

This repository is a clean rebuild. It does **not** claim to recover the historical repository or the missing 60-response pilot receipts described in earlier assignments.

- Protocol v2: drafted and machine-validated.
- Test prompts: 60/60 drafted and machine-validated. All 60 reference and
  constraint cards now contain review-ready anchors, exclusions, and
  authoritative sources; the three personal reviews and sign-offs remain.
- Public models: installed and smoke-tested on the study Mac; exact Ollama
  digests and template hashes are recorded in `config/model_artifacts.json`.
- KazLLM: authenticated official Q4_K_M artifact imported and smoke-tested;
  source SHA-256 and Ollama metadata are frozen in the repository.
- Final 240 test responses: not collected yet.
- Independent human labels: not collected yet.
- Confirmatory results: unavailable until collection, two independent ratings, and adjudication are complete.
- Submission artifacts: an integrated manuscript, an official-template ACM
  submission copy, draft cover letter,
  10-slide defense PDF, journal-fit statement and criteria matrix are built and
  visually checked. They deliberately contain no invented inferential result.

Read `docs/EXECUTION_STATUS.md` for the exact completed/blocked boundary. The
repository deliberately fails closed: it cannot collect the test set until the
prompt cards, three signoffs, model-artifact manifest, and freeze manifest all
agree.

Historical assignments are retained under `docs/archive/` as provenance, not as executable evidence for the final results.

Canonical repository: <https://github.com/qsheker/kazakh-llm-error-study>

## Submission artifacts

- `deliverables/Kazakh_LLM_Study_Manuscript.docx` — integrated ACM-style
  manuscript with declarations and appendices.
- `deliverables/Kazakh_LLM_Study_ACM_Submission.docx` — the same controlled
  manuscript transferred into the official one-column ACM Word style set.
- `deliverables/Cover_Letter_TALLIP.docx` — one-page draft cover letter; the
  red warning must be removed only after the final evidence gate passes.
- `output/pdf/Kazakh_LLM_Defense_Deck.pdf` — 10-slide defense deck.
- `docs/JOURNAL_FIT_STATEMENT.md` — completed primary/backup journal record.
- `docs/CRITERIA_MATRIX.md` — criterion-by-criterion status and evidence map.

Rebuild the two Word artifacts with:

```bash
.venv/bin/python scripts/build_manuscript.py
.venv/bin/python scripts/build_cover_letter.py
```

Rebuild the official-template copy without overwriting the working manuscript:

```bash
.venv/bin/python scripts/fetch_acm_template.py tmp/acm_submission_template.docx
.venv/bin/python scripts/build_acm_manuscript.py \
  --source deliverables/Kazakh_LLM_Study_Manuscript.docx \
  --template tmp/acm_submission_template.docx \
  --output deliverables/Kazakh_LLM_Study_ACM_Submission.docx
```

`scripts/build_defense_pdf.py` packages the ten slide PNG exports from the live
presentation workspace into the canonical PDF. The reviewed PDF is committed;
the script requires an explicit export directory and output path so it cannot
silently package stale slides.

## Team and accountable work

| Person | Primary accountable work |
|---|---|
| Aldiyar Zhaksylyk | Mac model setup, collection, repository, receipts, reproducibility, technical coordination, blinded adjudication |
| Yerkebulan Rakhymbay | Automated tests, statistics and interpretation, complete independent Rater 1 annotation |
| Iliyas Aitzhan | Complete independent Rater 2 annotation, manuscript integration, numerical consistency, journal fit, final QA |

All contributions must be supported by commits, signed review records, annotation files, execution receipts, or documented reviews. The three-person team has instructor approval even though the supplied general criterion states a maximum of two; the team should retain written evidence of that exception if available.

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

Test collection is programmatically locked while `config/protocol.json` remains `draft_pending_three_person_signoff`. Each reviewer must inspect the 60 cards and run their own command from `protocol/signoffs/README.md`; this prevents accidental test-set exposure before the signed review and freeze.

## Evidence and recovery rules

- Every request writes an `.inflight` marker before contacting Ollama.
- A completed receipt is reused only when its saved request exactly matches.
- An ambiguous timeout blocks automatic retry; deleting the marker merely to obtain a cleaner answer is prohibited.
- Poor, short, repetitive, refused, off-task, and truncated responses are retained.
- The model snapshot is compared before and after collection.
- Raw responses are immutable inputs; normalization and tokenization create derived copies.
- No human label may be inferred from detector output.

## Human annotation boundary

Yerkebulan and Iliyas must independently annotate all 240 blinded test responses. Automatic Latin/fastText candidates are hidden until both original label files and the adjudicated gold file are frozen. This repository can prepare, validate, merge, and analyze their work; it must not fabricate two independent human raters.

The evidence pipeline is explicit:

```bash
.venv/bin/python scripts/validate_annotation_workbook.py annotations/rater_1/final_test_v2__rater_1.xlsx --expected-responses 240
.venv/bin/python scripts/validate_annotation_workbook.py annotations/rater_2/final_test_v2__rater_2.xlsx --expected-responses 240
.venv/bin/python scripts/prepare_adjudication.py annotations/rater_1/final_test_v2__rater_1.xlsx annotations/rater_2/final_test_v2__rater_2.xlsx --expected-responses 240
.venv/bin/python scripts/analyze_final.py
```

The validation and agreement steps remain blinded. The final analysis opens the
private model mapping only after the adjudicated files have been frozen.

## Reproducing results

The final release will expose a single reproduction command after the 240 receipts and adjudicated labels exist. Until then, any generated table is a readiness artifact, not a final result. `final` must not be tagged before all checks in `docs/RELEASE_CHECKLIST.md` pass. The manuscript and deck are therefore final-quality containers, not false claims that the human study is already complete.

The machine-enforced release audit is:

```bash
.venv/bin/python scripts/release_gate.py
```

It exits nonzero and names every missing evidence item until the protocol,
receipts, two original ratings, adjudication, final analysis, institutional
records, outside reproduction, public remote, and clean worktree all exist.

## Ethics and data statement

The study evaluates locally generated text and does not intentionally collect external participant data or personal information. The three annotators are the authors. No formal ethics approval or exemption has been evidenced in the supplied materials; the manuscript must state this accurately and the team must confirm institutional requirements with the instructor before submission.

## Licences

Project software is MIT-licensed. Project-authored prompts, protocols and
documentation are CC BY 4.0. Third-party resources, archived coursework and
model artifacts retain their original terms; see `DATA_LICENSE.md` and
`resources/PROVENANCE.md`.
