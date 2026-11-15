# Prompt Review and Freeze Checklist

This checklist remains a defense-preparation aid. The frozen protocol uses the
coordinator-reported instructor authorization record and does not fabricate
three personal signatures.

## Aldiyar — authorship and file integrity

- [ ] Exactly 60 rows: 30 educational and 30 public-information.
- [ ] Every 5×6 domain/form cell occurs once.
- [ ] Prompt text is entirely Kazakh and does not contain answer hints.
- [ ] CSV fields and version are complete.
- [ ] Validation script passes and hashes are recorded.

## Yerkebulan — balance and leakage

- [ ] No exact or close duplicate within the test set.
- [ ] No test item repeats or closely paraphrases any of the 20 dev prompts.
- [ ] Every prompt can be answered offline without live prices, schedules, or news.
- [ ] Difficulty and instruction count are reasonably balanced across task blocks.
- [ ] Formal inclusion/exclusion criteria are satisfied.

## Iliyas — language and interpretability

- [ ] Kazakh wording is grammatical and unambiguous.
- [ ] Each prompt belongs to its declared task/domain/form.
- [ ] Required components can be scored from a frozen card.
- [ ] No invented local rule is required to answer.
- [ ] No medical, legal, financial, or other high-risk personalized advice is requested.

## Optional personal review record

| Name | Decision | Date/time | Git commit | Signature or verified account record |
|---|---|---|---|---|
| Aldiyar Zhaksylyk | Pending | | | |
| Yerkebulan Rakhymbay | Pending | | | |
| Iliyas Aitzhan | Pending | | | |

The executable freeze is recorded in `protocol/freeze_manifest.json` with the
status `frozen_joint_ai_assisted_coordinator_confirmed`. Optional personal review
records may be added later but must only be created by the named person.
