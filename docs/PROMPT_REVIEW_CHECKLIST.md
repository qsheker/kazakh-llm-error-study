# Prompt Review and Freeze Checklist

Protocol status remains draft until every box is reviewed by the named owner and all three sign the final record.

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

## Sign-off

| Name | Decision | Date/time | Git commit | Signature or verified account record |
|---|---|---|---|---|
| Aldiyar Zhaksylyk | Pending | | | |
| Yerkebulan Rakhymbay | Pending | | | |
| Iliyas Aitzhan | Pending | | | |

After all three approve, update `config/protocol.json` to `frozen_three_person_signoff`, record all frozen SHA-256 values, and make a dedicated freeze commit before any test inference.
