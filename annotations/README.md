# Annotation evidence

This directory stores human-produced evidence. Never synthesize or overwrite an
original rater workbook.

## Required sequence

1. Build two independently shuffled workbooks from the frozen run with
   `scripts/build_annotation_workbooks.py`.
2. Yerkebulan completes the Rater 1 workbook and Iliyas completes the Rater 2
   workbook without seeing the other file, model key, or detector output.
3. Validate both originals with `scripts/validate_annotation_workbook.py` and
   record their SHA-256 values.
4. Run `scripts/prepare_adjudication.py` to produce the blinded agreement report,
   rater event exports, response disagreements, and adjudication-log template.
5. Aldiyar adjudicates while model identities remain hidden. The final response
   labels and final events are saved under `annotations/adjudicated/` with an
   adjudicator and rationale for every event decision.
6. Freeze the gold files, then open the private model key and run
   `scripts/analyze_final.py`.

The final response CSV has one row per `blind_id` and the five response flags
`refusal`, `off_task`, `requirement_missing`, `repetition`, and
`fabricated_specificity`, each resolved to `yes` or `no`.

The final event CSV preserves the event columns from the workbooks and adds
`adjudicator` and `adjudication_rationale`. Every fragment and offset must still
match the immutable raw response.
