# Annotation Protocol v2 (Draft Before Calibration)

## Independence and blinding

Yerkebulan Rakhymbay (Rater 1) and Iliyas Aitzhan (Rater 2) annotate every test response independently in separately shuffled workbooks. They may see the prompt and its frozen reference/constraint card, but not the model identity, generation timing, the other rater's labels, or any automatic detector candidates.

Aldiyar Zhaksylyk coordinates files and adjudicates disagreements while model labels remain hidden. Original rater files are hashed and never overwritten. The private model key is opened only after the adjudicated gold file is frozen.

## Calibration

1. Training calibration: 12 dev responses, followed by discussion and rubric clarification.
2. Blinded qualification: 20 different dev responses, without discussion.
3. Proceed only when category-presence agreement is at least 80%, Cohen's kappa is at least 0.60 where defined, interval Krippendorff alpha for total primary counts is at least 0.67, and exact span-match F1 is at least 0.60. Exact span matching requires the same blind response, category, start offset, and exclusive end offset; no fuzzy boundary tolerance is used in the qualification gate.
4. If a threshold is missed, revise the rubric and repeat qualification on unused dev responses. Dev items never enter final results.

## Error event

An event is the smallest continuous fragment requiring one independent correction. Store the exact fragment, zero-based half-open character offsets, inclusive token indices, proposed correction, rationale, and any source used.

One event receives one primary category. For genuinely overlapping interpretations, use this priority:

1. `code_switching`
2. `semantic`
3. `grammatical`
4. `lexical`

Separate independent errors are separate events. A repeated occurrence at a different location is a new event. Spelling, punctuation, capitalization, and spacing are surface flags and do not increase the primary endpoint. Uncertain cases use `needs_adjudication`; never force certainty.

## Primary categories

- `grammatical`: incorrect word formation, inflection, agreement, government, or syntax.
- `lexical`: an unsuitable word or combination in an otherwise grammatically possible construction. A mere style preference is not an error.
- `semantic`: a proposition contradicting an explicit prompt condition or a frozen reference card, including invented concrete facts.
- `code_switching`: an unrequested non-Kazakh span. Proper names, established borrowings, identifiers, and explicitly requested quotations are exempt.

Missing a requested component is a response-level `requirement_missing` flag, not automatically a semantic event.

## Response-level fields

Word count, 150–200 compliance, and truncation are computed from raw text and the Ollama receipt. Both raters independently label:

- `refusal`: direct refusal or inability claim;
- `off_task`: the main content does not answer the prompt;
- `requirement_missing`: one or more explicit prompt/card requirements are absent;
- `repetition`: repeated wording or proposition without a new function;
- `fabricated_specificity`: unsupported prices, schedules, rules, addresses, or other verifiable specifics.

Record which requirements are missing. These flags remain separate from the linguistic error rate.

## Adjudication

The merge step identifies disagreements without model labels. Each final decision records the adjudicator and rationale. Originals remain immutable. Agreement statistics are computed on original labels before adjudication and reported even if weak.

`scripts/validate_annotation_workbook.py` checks completeness, allowed values,
unique event identifiers, offsets, exact fragments, token ranges, corrections,
and rationales. `scripts/prepare_adjudication.py` then computes agreement and
exports both event sets and response disagreements without opening the model
key.
