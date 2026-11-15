# Annotation evidence

This directory stores the blinded joint-team gold workbook and review evidence.
The workflow is AI-assisted and must not be represented as two independent
human annotations.

## Required sequence

1. Build one blinded workbook from the frozen run with
   `scripts/build_annotation_workbooks.py`.
2. AI tools may propose draft flags and events without model identities or
   detector candidates.
3. The team reviews and resolves every response and event. Record exactly one
   responsible named team member, `approved` status, AI-assistance flag and
   review timestamp per blind ID in `team_gold/team_review_log.csv`.
4. Validate the final workbook with `scripts/validate_annotation_workbook.py`
   and freeze its SHA-256 together with the review log.
5. Run `scripts/analyze_final.py`; only then may the private model key be used.

The workbook builder also creates `team_gold/team_review_log.csv` with 80
pending blind IDs assigned to each team member. This is an equal responsibility
plan, not evidence that a review occurred. The assigned person must complete the
row after reviewing the response. Rerunning the builder validates and preserves
an existing log instead of overwriting it.

The final response fields are `refusal`, `off_task`, `requirement_missing`,
`repetition`, and `fabricated_specificity`, resolved to `yes` or `no`. Every
event requires exact offsets, a matching fragment, correction, rationale and
`needs_adjudication=no`.
