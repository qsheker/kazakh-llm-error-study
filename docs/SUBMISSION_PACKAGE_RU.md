# Что сдавать на финале

## Основной пакет

1. `deliverables/Kazakh_LLM_Study_ACM_Submission.docx` — итоговая статья в
   официальном ACM Word template. Сейчас это честный pre-results draft; после
   анализа в нём должны появиться сгенерированные Results и conclusion.
2. `deliverables/Cover_Letter_TALLIP.docx` — одностраничное письмо. Красную
   пометку **DRAFT — DO NOT SUBMIT** удалить только после release gate.
3. `output/pdf/Kazakh_LLM_Defense_Deck.pdf` — PDF презентации, 8–12 слайдов
   (сейчас 10). После анализа заменить evidence-gate слайды на реальные
   результаты и проверить все повторяющиеся числа.
4. `docs/JOURNAL_FIT_STATEMENT.md` — Appendix A: основной журнал TALLIP,
   резервный журнал, Scopus/policy evidence и обоснование выбора.
5. `docs/RELEASE_CHECKLIST.md` — Appendix B: фактически выполненный checklist.
6. Ссылка на публичный GitHub repository и финальный release/tag `final`.
   Тег создаётся только после успешного `scripts/release_gate.py`.

## Репозиторий / release archive

В release должны войти код, frozen protocol, prompt/reference bundle,
environment/model manifests, все 240 receipts, incident evidence, reviewed
team-gold workbook, review log и автоматически сгенерированные Results.

Не включать:

- `data/blinding/private_model_key.csv` в публичный Git до предусмотренного
  шага unblinding/release;
- model binaries, `.venv`, access tokens или локальные Ollama blobs;
- старую Windows `.deps` папку;
- незаполненные evidence templates вместо реальных подтверждений.

## Реальные подтверждения от людей/университета

- `evidence/similarity_report.pdf` — настоящий отчёт системы университета;
- `evidence/ethics_determination.pdf` — решение преподавателя/институции;
- письменное разрешение команды из трёх человек, если преподаватель может его
  дать файлом или сообщением;
- `reference_verification.json` — каждый из трёх действительно прочитал и
  проверил 28 источников;
- `all_author_approval.json` и `presentation_review.json` — одобрение точных
  финальных хэшей;
- `reproduction.json` — воспроизведение человеком вне команды.

Формы находятся в `evidence/templates/`, но сами шаблоны доказательством не
являются.

## Что ещё не позволяет нажать Submit

На 16 ноября 2026 года inference завершён (240/240), но финал блокируют:

1. реальные 80 + 80 + 80 человеческих проверок blinded team gold;
2. автоматически сгенерированные статистика, таблицы и figure после review;
3. перенос этих чисел в manuscript и slides с numerical audit;
4. similarity/ethics/reference/author approvals и outside reproduction;
5. чистый commit, GitHub CI, release archive и тег `final`.

До выполнения этих пунктов можно сдавать проект преподавателю как
**pre-results review package**, но нельзя выдавать его за завершённую
result-bearing journal submission.
