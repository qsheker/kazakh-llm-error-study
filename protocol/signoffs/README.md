# Sign-off records

Each team member creates their own JSON record after reviewing the exact test-set hash. Do not create records on another person's behalf.

Required example:

```json
{
  "name": "Aldiyar Zhaksylyk",
  "decision": "approved",
  "reviewed_utc": "2026-11-15T00:00:00Z",
  "test_sha256": "...",
  "instruction_sha256": "...",
  "reference_bundle_sha256": "...",
  "model_artifacts_sha256": "...",
  "review_notes": "All assigned checklist items completed."
}
```

Expected filenames are `aldiyar.json`, `yerkebulan.json`, and `iliyas.json`.

After personally reviewing all 60 cards, each reviewer should run their own
command from the repository root. Replace the notes with a concise description
of what that reviewer checked:

```bash
.venv/bin/python scripts/create_signoff.py --signer aldiyar --approve --notes "Reviewed all prompts, anchors, exclusions, and sources."
.venv/bin/python scripts/create_signoff.py --signer yerkebulan --approve --notes "Reviewed all prompts, anchors, exclusions, and sources."
.venv/bin/python scripts/create_signoff.py --signer iliyas --approve --notes "Reviewed all prompts, anchors, exclusions, and sources."
```

No one may run a command for another person. The helper refuses to overwrite an
existing sign-off and always binds the decision to the current prompt, source,
instruction, and model-artifact hashes.
