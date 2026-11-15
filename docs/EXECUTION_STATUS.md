# Execution status

Snapshot: 2026-11-15, Asia/Almaty.

## Completed and executed

- Rebuilt the project as a native macOS/Python repository instead of carrying
  over the supplied 115 MB Windows dependency bundle.
- Drafted and validated 60 Kazakh test prompts with the frozen 30/30 task split
  and balanced domain/form matrices.
- Replaced all 60 empty reference-card placeholders with review-ready factual
  anchors, acceptable variants, prohibited claims, and authoritative sources.
  Automated tests verify complete coverage and reject pending markers.
- Installed `qwen3:8b`, `llama3.1:8b`, and `gemma3:12b` in Ollama on the study
  Mac; recorded immutable model content, template, parameters, and system hashes.
- Authenticated to the gated official ISSAI repository, downloaded the pinned
  KazLLM Q4_K_M GGUF, froze SHA-256
  `1a37de3ca5e9fb3754ac070f8a5d1dc328c2ac43217daea506bf1877fab76dba`,
  imported it as `kazllm:8b-q4_k_m`, and captured the complete four-model
  artifact manifest.
- Captured the Mac/Ollama/Python environment without serial number, hardware
  UUID, username path, or access tokens.
- Executed one retained dev smoke response per public model using the intended
  controls. Llama reached the 768-token boundary and repeated text; that outcome
  remains evidence and was not regenerated.
- Executed a two-request Qwen determinism check; the response SHA-256 matched.
- Executed the KazLLM dev smoke test with the frozen controls: 109 words and
  normal `stop` completion.
- Executed the complete 80-request dev calibration run across all four models:
  80 receipts, 80 accounted requests, zero in-flight markers, identical
  generation controls, and unchanged model metadata. Machine-local manifest
  paths were normalized without altering any receipt.
- Selected a balanced, disjoint calibration set and built four blinded Excel
  workbooks: 12 training responses and 20 qualification responses for each of
  Yerkebulan (Rater 1) and Iliyas (Rater 2). Both phases have public read-only
  field integrity manifests; the private model mapping is excluded from Git.
- Added and tested prompt validation, fail-closed collection, request receipts,
  annotation workbook handling, detectors, and frozen statistical procedures.
- Added strict workbook validation, blinded agreement/adjudication packaging,
  full H1-H4 analysis generation, input-hash manifests, and a machine-enforced
  release gate. The final analysis command cannot run without the immutable
  receipts, private mapping, resolved human labels, adjudication rationales,
  reviewed detector exemptions, and language-ID model.
- Verified the primary and backup journals in the live Scopus Sources interface.
- Built and visually checked the working manuscript, a 16-page copy transferred
  into the official ACM Word template, the one-page controlled-draft cover
  letter, and 10-slide defense PDF. The two manuscript copies pass the automated
  accessibility audit with zero high, medium, or low findings; their ZIP
  containers are valid. These artifacts intentionally report the executed
  readiness evidence but no fabricated confirmatory result.
- Re-ran all 29 repository tests, Ruff, the 60-prompt protocol validator, the
  80-receipt run validator, workbook structure/integrity checks, and the
  four-model Ollama preflight on this Mac on 2026-11-15.
- Created the public GitHub repository and pushed the verified local history to
  `https://github.com/qsheker/kazakh-llm-error-study` as `main`.

## Intentionally blocked

1. **Protocol freeze.** All 60 populated reference cards still require human
   verification, and Aldiyar, Yerkebulan, and Iliyas must personally sign the
   same hash bundle.
2. **Test inference.** The 240-response collection cannot start until (1) is
   resolved. The collector enforces this boundary.
3. **Independent labels.** Yerkebulan and Iliyas must personally produce their
   two complete annotation files. The repository must not synthesize them.
4. **Final results and result-bearing submission revision.** The submission
   containers exist, but their quantitative Results, final abstract conclusion,
   result slides, and release metadata depend on immutable test receipts, two
   frozen ratings, adjudication, and generated statistics. No placeholder is
   represented as an observed result.
5. **External gates.** Personal source reading, ethics determination,
   university similarity report, written evidence of the approved three-person
   exception, outside-team reproduction, final release URL, and all-author
   approval remain human or institutional actions.

## Next executable sequence

```bash
.venv/bin/python scripts/validate_protocol.py
# Yerkebulan and Iliyas complete their own training and qualification files,
# then validate and adjudicate qualification while still blinded.
# complete cards + three signoffs, then:
.venv/bin/python scripts/freeze_protocol.py
.venv/bin/python scripts/collect.py --dataset test --preflight
.venv/bin/python scripts/collect.py --dataset test --send --run-id final_test_v2
.venv/bin/python scripts/build_annotation_workbooks.py runs/final_test_v2 \
  --output annotations --references data/references \
  --mapping data/blinding/private_model_key.csv
```

The later merge, analysis, manuscript, and slide steps must use the frozen raw
inputs; they are not unlocked merely by a successful inference run.
