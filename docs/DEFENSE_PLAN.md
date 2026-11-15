# Three-person defense plan

The instructor-approved three-person exception should be evidenced in writing
if possible. The plan below balances accountable intellectual impact; it does
not invent equal Git commit counts or pretend the implementation workload was
identical.

## Ownership and defensible impact

| Person | Owns before the defense | Must be able to defend | Evidence |
|---|---|---|---|
| Aldiyar Zhaksylyk | Local model execution, frozen artifacts, data provenance, repository, reproducibility, blinded adjudication | Why the four artifacts are comparable enough; request controls; freeze and recovery rules; why no failed or ugly response was regenerated; adjudication without detector leakage | Model digests, environment receipt, raw request receipts, freeze manifest, adjudication log, clean reproduction |
| Yerkebulan Rakhymbay | Complete independent Rater 1 labels, tests, statistical analysis and interpretation | Primary endpoint; Friedman permutation test; Kendall's W; Pratt pairwise tests with Holm correction; bootstrap intervals; missing/zero-word handling; difference between confirmatory H1/H2 and exploratory H3/H4 | Original hashed Rater 1 workbook, test runs, generated tables/figures, analysis review record |
| Iliyas Aitzhan | Complete independent Rater 2 labels, manuscript integration, numerical consistency, journal fit and final QA | Annotation rules and disagreements; why TALLIP fits; how every number traces to generated outputs; limitations; data/ethics statement; reference and template compliance | Original hashed Rater 2 workbook, manuscript review checklist, consistency audit, journal/template record |

Each member owns one indispensable evidence chain. Removing any one chain makes
the final conclusions invalid: no reproducible observations without Aldiyar, no
independent statistical claim without Yerkebulan, and no second rating or
integrated research report without Iliyas.

## Speaking order (10-minute version)

1. **Aldiyar, 0:00–3:20** — problem, research questions, frozen design, models,
   Mac execution, provenance safeguards.
2. **Yerkebulan, 3:20–6:40** — outcome definitions, annotation-derived counts,
   agreement, statistical tests, main tables and effect sizes.
3. **Iliyas, 6:40–10:00** — integrated findings, error examples, limitations,
   journal fit, reproducibility/data statement, conclusion.

For a shorter defense, preserve the same one-third proportions. Do not let one
person narrate another person's evidence slide.

## Cross-question rule

The named owner answers first. A second member may add one precise point; Aldiyar
does not automatically rescue every answer. Everyone must still know the whole
study well enough to explain the design, the main result, the largest
limitation, and why no result was fabricated.

## Minimum rehearsal gate

- Each person gives their section twice without reading a script.
- Each person answers five hostile questions from the other two.
- Every spoken number is checked against a generated table, not copied by hand.
- The team can explain why `240` is the planned number of responses and whether
  the accounted-for total contains any explicit failures.
- The team can state that the old three-response evidence is a pilot artifact,
  not part of the confirmatory test set.
- Nobody claims independent annotation until the two original workbooks exist,
  are frozen, and their hashes are recorded.

## Likely hostile questions

1. Why compare a 12B model with 8B models, and what conclusion is therefore not
   allowed?
2. Why is deterministic decoding useful here, and what does it not guarantee?
3. Why are purposeful prompts not a representative sample of all Kazakh usage?
4. How did you prevent automatic detectors from influencing human labels?
5. What happens if a response is empty, truncated, repetitive, or times out?
6. Why is the Friedman design blocked by prompt rather than treated as 240
   independent observations?
7. Why are H3/H4 exploratory?
8. What evidence proves the exact model artifact rather than just its tag?
9. What can be concluded from one quantized artifact per model family?
10. Why is there no ethics approval number in the report?

The acceptable answers must match `protocol/analysis_plan.md`,
`protocol/annotation_protocol.md`, and the final generated evidence. If the
answer requires a number that is not yet generated, say that it is pending; do
not improvise it.
