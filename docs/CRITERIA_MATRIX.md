# Final Project Criteria Matrix

Assessment date: 2026-11-15. This matrix distinguishes built evidence from work that only the three human authors can complete. “Blocked” is not a placeholder result; it is a safeguard against fabrication.

## Final submission package

| Required item | Status | Evidence / remaining gate |
|---|---|---|
| Final manuscript in target template | Official-template review draft implemented; results gated | `deliverables/Kazakh_LLM_Study_ACM_Submission.docx`; controlled manuscript transferred into the official one-column ACM Word style set, 4,500–7,500-word core range, 28 references, declarations, numbered table captions and appendices. Replace the Results contract only with generated evidence. |
| Journal Fit Statement (Appendix A) | Implemented | `docs/JOURNAL_FIT_STATEMENT.md`; primary and backup titles, ISSNs, Scopus records, metrics, official URLs, integrity checks, recent related papers, policies and decision. Human authors must read the three cited TALLIP papers. |
| One-page cover letter | Implemented as controlled draft | `deliverables/Cover_Letter_TALLIP.docx`; one page and visibly marked not to submit before the evidence gate. |
| Repository and release tag `final` | Repository implemented; tag intentionally blocked | Code, tests, environment, model and resource provenance are present. Creating `final` before 240 accounted requests, two frozen ratings, adjudication, reproduction and approvals would violate the criterion. |
| Presentation PDF, 8–12 slides | Implemented, final results gated | `output/pdf/Kazakh_LLM_Defense_Deck.pdf`; 10 visually checked slides. Generated result slides must replace the evidence-gate framing after analysis. |
| Submission Readiness Checklist (Appendix B) | Implemented, unchecked honestly | `docs/RELEASE_CHECKLIST.md` and manuscript Appendix B. Boxes remain open until evidence exists. |

## Evaluation criteria

| Criterion | Points | Status | Evidence / remaining gate |
|---|---:|---|---|
| A1. Title, abstract, introduction, contributions | 8 | Structure met; quantitative abstract result blocked | Specific nine-word title; 200–250-word abstract; explicit RQs/H1–H4; four enumerated contributions. Final quantitative result and conclusion require generated tables. |
| A2. Related work | 7 | Implemented; author reading verification pending | Thematic synthesis, closest-study comparison table, explicit gap, 28 references, and three recent TALLIP papers. Each human author must actually read and verify the sources sampled by the instructor. |
| A3. Materials and methods | 10 | Implemented and machine-tested | Balanced 60-prompt design; exact four artifacts; frozen controls; failure/retry rules; two-rater blinding; adjudication; endpoint; permutation Friedman, Kendall’s W, Pratt-Holm comparisons and clustered bootstrap; ethics and reproducibility settings. |
| A4. Results | 12 | Blocked by genuine missing observations | No 240-response test collection, two independent human label files or adjudicated gold file exists. The reporting contract and analysis code are ready; inventing numbers would trigger the course zero rule. |
| A5. Discussion and conclusion | 8 | Limitations implemented; final interpretation blocked | Threats to validity, unequal model sizes/templates, purposeful sampling, imperfect blinding, detector limitations and no-overclaim rule are present. Comparison with observed findings waits for A4. |
| A6. Academic writing and formatting | 5 | Official-template review draft implemented; institutional checks pending | Academic English, official one-column ACM Word styles, 28 DOI/URL-backed references, numbered and text-cited tables, full 16-page visual DOCX QA and accessibility audit with zero findings. University similarity report and personal source-reading declarations are human/institutional steps. |
| B. Journal fit and cover letter | 5 | Implemented with time-sensitive recheck | TALLIP primary and LRE backup verified; scope decision, recent articles, policies and one-page draft letter supplied. Scopus/policy/APC facts must be rechecked at actual submission. |
| C. Reproducibility package | 12 | Technical layer and public remote implemented; final reproduction blocked | MIT code licence, CC BY 4.0 data/documentation licence, environment capture, hashes, fail-closed collector, tests, README and public GitHub repository are present. Final logs, release archive, outside-team reproduction and `final` tag require the completed human study. |
| D1. Team presentation | 10 | 10-slide final-quality container; result slides blocked | Clear problem, RQs, method, artifacts, annotation, statistics, executed readiness evidence, evidence gate and ownership. Final numerical result and error example must come from generated evidence. |
| D2. Individual defence | 23 | Preparation implemented; performance is human | Equal 3:20 speaking blocks, accountable evidence chains, cross-question rule, rehearsal gate and ten hostile questions in `docs/DEFENSE_PLAN.md`. Each member must rehearse and answer independently. |

## Structure-specific checks

- Core manuscript length: 4,682 words before the References heading when table cells are included, within the 4,500–7,500 course range; references and appendices are excluded.
- Abstract: no citations and within the requested range; its final-result sentences are intentionally withheld until real results exist.
- Keywords: five terms and no exact repetition of the title phrase.
- Related work: thematic synthesis plus a closest-study comparison table.
- Methods: full design, data, variables, procedure, baselines, analysis, ethics and reproducibility settings.
- Declarations: data/code availability, CRediT, AI use, funding, conflicts and ethics.
- References: 28 entries; more than half are from 2021–2026 after addition of three 2025 TALLIP articles.
- Presentation: 10 pages/slides, within the required 8–12 range.
- Three-person exception: the README and defense plan record the instructor-approved exception; retain the instructor’s written approval with the submission package.

## Irreducible human completion sequence

1. All three authors verify the 60 populated reference cards and sign one freeze hash bundle with `scripts/create_signoff.py`.
2. Aldiyar runs the locked collector once for all 240 model-prompt pairs and resolves any ambiguous timeout by the documented rule, never by quality-based regeneration.
3. Yerkebulan and Iliyas independently annotate every blinded response and freeze/hash their original files.
4. Aldiyar adjudicates disagreements while model labels and detector candidates remain hidden; freeze the gold file, then open the key.
5. Generate accounting, agreement, model, pairwise, sensitivity and detector outputs; propagate them mechanically into manuscript and slides; audit every repeated number.
6. All authors personally verify references, approve the manuscript, complete the similarity check and obtain the institution/instructor ethics determination.
7. A person outside the team reproduces the Results from the README on the documented Mac environment.
8. The public GitHub remote now exists; after the evidence gate, create the release archive, run the secret/licence audit, record the release URL, and only then create the signed `final` release tag.
