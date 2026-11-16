# Final Release Checklist

Machine audit: 2026-11-16. `validate_run.py` passes for 240/240 receipts;
`validate_annotation_workbook.py` passes for the reviewed 240-response team gold;
the final analysis and result-bearing manuscript are generated. `release_gate.py`
still reports `ready: false` because external evidence and the clean-release steps
remain outstanding.

- [x] Protocol and prompt freeze precede all test receipts.
- [x] Four model digests, templates, Ollama version, Mac hardware, and package lock are recorded.
- [x] Exactly 240 completed or explicitly failed test requests are accounted for.
- [x] No quality-based regeneration occurred; the sole pre-generation runner-load failure has preserved incident evidence and an identical-payload retry.
- [x] One reviewed joint-team gold workbook and its 240-row review log are hashed and source-bound.
- [x] AI assistance is disclosed; no duplicated team file is described as independent human reliability evidence.
- [x] Every manuscript results table and the primary figure are reproduced from hashed inputs.
- [x] H1–H2 and H3–H4 are reported with their frozen confirmatory/exploratory status.
- [x] Limitations disclose unequal model sizes/templates, purposeful prompts, one local quantized artifact per family, and imperfect stylistic blinding.
- [x] At least 25 references are present and at least half meet the course recency rule; personal author reading remains separately gated.
- [x] Primary and backup Scopus journals and the verified template/policies are recorded.
- [ ] Independent clean reproduction succeeds on the documented Mac environment.
- [ ] Manuscript, 8–12 slides, contribution evidence, README, raw/derived provenance, and data statement agree numerically.
- [x] No secret token, private blinding key, model binary, `.venv`, or Windows `.deps` is committed.
- [ ] Release tag `final` is created only after all checks pass.

Operational instructions and the exact submit-now boundary are in
`docs/FINAL_SUBMISSION_AND_DEFENSE_RU.md`.
