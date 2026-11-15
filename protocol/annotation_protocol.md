# Annotation Protocol v2.1 (Joint Team AI-Assisted)

## Provenance and review model

The final labels are one team-consensus gold set, not two independent human
ratings. AI assistance may propose spans, categories, corrections, rationales,
response-level flags, and consistency checks. Those proposals are drafts. The
three named students remain responsible for reviewing, editing, accepting, and
defending the final labels.

The team works from blinded response IDs. Model identity, timings, and automatic
detector outputs remain hidden until the gold set is frozen. The final gold
workbook and its exported CSV files are hashed. A review log records, for every
response, the responsible reviewer, review status, and any material change to
an AI draft. No Cohen's kappa, Krippendorff alpha, span F1, or other
inter-annotator reliability value is reported as evidence from this joint
workflow.

Logical responsibility is divided without pretending that the work was
independent: Aldiyar owns protocol, collection, provenance, and final audit;
Yerkebulan owns test verification, label quality control, and statistical
checks; Iliyas owns gold-label and result integration plus visualization checks.
All three must be able to explain the rubric and defend the final result.

## Calibration

The retained development calibration bundle is used to learn the schema, test
the rubric, and expose ambiguous examples. Team-assisted calibration files may
be used for consistency checks but are not independent-rater evidence and are
not used to estimate human reliability. Development items never enter final
results.

## Error event

An event is the smallest continuous fragment requiring one independent
correction. Store the exact fragment, zero-based half-open character offsets,
inclusive token indices, proposed correction, rationale, and any source used.

One event receives one primary category. For genuinely overlapping
interpretations, use this priority:

1. `code_switching`
2. `semantic`
3. `grammatical`
4. `lexical`

Separate errors are separate events. A repeated occurrence at a different
location is a new event. Spelling, punctuation, capitalization, and spacing are
surface flags and do not increase the primary endpoint. An unresolved case is
marked `needs_adjudication` in a draft and must be resolved before the final gold
set is frozen.

## Primary categories

- `grammatical`: incorrect word formation, inflection, agreement, government,
  or syntax.
- `lexical`: an unsuitable word or combination in an otherwise grammatically
  possible construction. A mere style preference is not an error.
- `semantic`: a proposition contradicting an explicit prompt condition or a
  frozen reference card, including invented concrete facts.
- `code_switching`: an unrequested non-Kazakh span. Proper names, established
  borrowings, identifiers, and explicitly requested quotations are exempt.

Missing a requested component is a response-level `requirement_missing` flag,
not automatically a semantic event.

## Response-level fields

Word count, 150–200 compliance, and truncation are computed from raw text and
the Ollama receipt. The team resolves these review fields to `yes` or `no`:

- `refusal`: direct refusal or inability claim;
- `off_task`: the main content does not answer the prompt;
- `requirement_missing`: one or more explicit prompt/card requirements are
  absent;
- `repetition`: repeated wording or proposition without a new function;
- `fabricated_specificity`: unsupported prices, schedules, rules, addresses, or
  other verifiable specifics.

Record which requirements are missing. These flags remain separate from the
linguistic error rate.

## Consensus and freeze

AI drafts and intermediate files are kept separate from the final gold set.
Every final event must have valid offsets, a matching exact fragment, a
correction, and a rationale. Every response-level flag must be resolved. The
team review log must cover all 240 blind IDs before analysis. The gold files,
review log, frozen protocol, and immutable model receipts are the only inputs to
the final analysis.

The detector is evaluated against the reviewed team gold; it is never used as
an independent annotator or as proof of human agreement. Limitations must state
that joint AI-assisted review cannot estimate independent human reliability and
may propagate shared errors.
