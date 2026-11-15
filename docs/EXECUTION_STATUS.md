# Execution status

Snapshot: 2026-11-15, Asia/Almaty.

## Completed and executed

- Rebuilt the project as a native macOS/Python repository instead of carrying
  over the supplied 115 MB Windows dependency bundle.
- Drafted and validated 60 Kazakh test prompts with the frozen 30/30 task split
  and balanced domain/form matrices.
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
- Added and tested prompt validation, fail-closed collection, request receipts,
  annotation workbook handling, detectors, and frozen statistical procedures.
- Verified the primary and backup journals in the live Scopus Sources interface.

## Intentionally blocked

1. **Protocol freeze.** All 60 reference cards still require human verification,
   and Aldiyar, Yerkebulan, and Iliyas must sign the same hash bundle.
2. **Test inference.** The 240-response collection cannot start until (1) is
   resolved. The collector enforces this boundary.
3. **Independent labels.** Yerkebulan and Iliyas must personally produce their
   two complete annotation files. The repository must not synthesize them.
4. **Final results/manuscript/slides.** These depend on immutable test receipts,
   two frozen ratings, adjudication, and generated statistics. No placeholder is
   represented as an observed result.

## Next executable sequence

```bash
.venv/bin/python scripts/validate_protocol.py
# complete cards + three signoffs, then:
.venv/bin/python scripts/freeze_protocol.py
.venv/bin/python scripts/collect.py --dataset test --preflight
.venv/bin/python scripts/collect.py --dataset test --send --run-id final_test_v2
.venv/bin/python scripts/build_annotation_workbooks.py
```

The later merge, analysis, manuscript, and slide steps must use the frozen raw
inputs; they are not unlocked merely by a successful inference run.
