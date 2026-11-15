# Analysis Plan v2

## Hypothesis hierarchy

- H1, primary confirmatory: at least one of the four configurations differs in total primary-error rate per 100 word tokens.
- H2, planned confirmatory: KazLLM has a lower rate than Llama 3.1 8B.
- H3, secondary exploratory: code-switching is the most frequent primary category across the three general-purpose models.
- H4, secondary exploratory: the response-level hybrid detector has higher F1 than the Latin-script baseline.

## Primary endpoint

For each non-empty response:

`100 × (grammatical + lexical + semantic + code-switching events) / word tokens`

A zero-word output has an undefined rate and is reported as a generation failure. Primary Friedman analysis uses prompt blocks with defined rates for all four models. Textual refusals and off-task answers are annotated and separately flagged. Truncated answers remain in the primary analysis and are excluded only in a sensitivity analysis.

## Confirmatory analysis

H1 uses a tie-corrected Friedman statistic with 99,999 label permutations within each prompt, seed 2417, alpha 0.05, and Kendall's W. Six two-sided pairwise Wilcoxon signed-rank tests use Pratt zero handling and Holm correction. Report rank-biserial correlation and mean response-rate differences with 95% cluster-bootstrap confidence intervals from 10,000 whole-prompt resamples stratified by task type, seed 2417.

H2 is supported only when H1 is significant, the Holm-adjusted KazLLM–Llama comparison is significant, the point estimate `KazLLM − Llama` is below zero, and its bootstrap interval is entirely below zero. Otherwise report that H2 was not supported; do not claim equivalence.

## H3

Pool adjudicated events and word tokens across Qwen, Llama, and Gemma. For each category compute `100 × total events / total word tokens`. Code-switching is descriptively most frequent only when its pooled rate exceeds all alternatives. Also report whole-prompt bootstrap intervals, contrasts, and mean response-level category rates. H3 remains exploratory.

## H4

Gold positive means at least one adjudicated code-switching event. Latin baseline positive means any non-exempt word token contains a Latin letter. fastText positive means any sentence or sliding three-word window is classified non-Kazakh with confidence at least 0.85. Hybrid positive is Latin OR fastText. The exemption file is frozen from dev evidence and documented rules before test labels.

Compute precision, recall, and F1 on all 240 responses. Estimate the hybrid-minus-Latin F1 difference with 10,000 whole-prompt cluster-bootstrap resamples. Undefined metrics remain undefined.

## Secondary and sensitivity analyses

Report category rates, error presence, foreign-token share, length compliance, truncation, repetition, refusal, off-task behavior, latency, generated tokens, and tokens/second. Stratify by task type and estimate a bootstrap model-by-task difference-in-differences. Sensitivity analyses exclude truncated answers, compare pooled with mean response rates, retain each pre-adjudication rater separately, and include surface errors separately.

An offset count model is exploratory. Interpret it only when convergence and dispersion diagnostics are acceptable; otherwise report instability and use the stratified paired results.
