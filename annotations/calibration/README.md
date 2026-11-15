# Dev calibration workbooks

The `dev_calibration_v2` subdirectory is generated only after all 80 dev
receipts pass `scripts/validate_run.py`. It contains four blinded instruments:
training and qualification workbooks for Rater 1 and Rater 2.

## Required order

1. Yerkebulan opens only `rater_1/*training*`; Iliyas opens only
   `rater_2/*training*`.
2. Both finish the 12 training responses independently. Then the team discusses
   disagreements and clarifies the rubric without changing those original files.
3. Both complete their 20-response qualification workbook independently and
   without discussion.
4. Validate both qualification files, then run `prepare_adjudication.py` with
   `--blinded-manifest qualification_blinded_manifest.json` and
   `--expected-responses 20` in a separate calibration output directory. The
   manifest makes any change to a read-only prompt, response, reference card,
   word count, or finish reason fail closed.
5. Proceed to test annotation only when all four frozen qualification thresholds
   in `protocol/annotation_protocol.md` pass. Otherwise revise the rubric and use
   different unused dev responses for another qualification round.

Do not inspect `data/blinding/dev_calibration_v2_key.csv`, the other rater's
folder, dev receipt filenames, model labels, or detector output before both
qualification files are frozen and hashed.

The workbooks are calibration evidence, not confirmatory study data. They must
never be merged into the 240 test responses or reported as model results.

Generated files:

- `rater_1/*training*` and `rater_1/*qualification*` — Yerkebulan only.
- `rater_2/*training*` and `rater_2/*qualification*` — Iliyas only.
- `training_blinded_manifest.json` and
  `qualification_blinded_manifest.json` — public immutable-field checks.
- `workbook_manifest.json` — workbook hashes bound to the public bundle.

The private file `data/blinding/dev_calibration_v2_key.csv` is intentionally
ignored by Git and must stay hidden until both qualification workbooks are
complete and hashed.
