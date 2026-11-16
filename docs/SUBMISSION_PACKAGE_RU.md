# Что сдавать на финале

Каноническая пошаговая инструкция находится в
`docs/FINAL_SUBMISSION_AND_DEFENSE_RU.md`. Этот файл сохраняет краткую карту
пакета.

## Основной пакет

1. `deliverables/Kazakh_LLM_Study_ACM_Submission.docx` — result-bearing статья
   в официальном ACM Word template с автоматически сгенерированными Results.
2. `deliverables/Cover_Letter_TALLIP.docx` — одностраничное result-bearing
   письмо; внешняя отправка остаётся gated до всех подтверждений.
3. `output/pdf/Kazakh_LLM_Defense_Deck.pdf` — PDF презентации, 8–12 слайдов
   (сейчас 10). Все повторяющиеся числа должны совпадать с
   `results/derived/final_test_v2/summary.json`.
   Редактируемая копия: `deliverables/Kazakh_LLM_Defense_Deck.pptx`.
4. `docs/JOURNAL_FIT_STATEMENT.md` — Appendix A: основной журнал TALLIP,
   резервный журнал, Scopus/policy evidence и обоснование выбора.
5. `docs/RELEASE_CHECKLIST.md` — Appendix B: фактически выполненный checklist.
6. Ссылка на публичный GitHub repository и финальный release/tag `final`.
   Тег создаётся только после успешного `scripts/release_gate.py`.
7. `deliverables/Final_Submission_and_Defense_Guide_RU.docx` — внутренняя
   инструкция команды; приложить преподавателю можно, в journal submission не
   включать.
8. Готовый пакет для преподавателя:
   `output/packages/Kazakh_LLM_Final_Course_Submission.zip`. Внутренний manifest
   фиксирует состав, SHA-256 и незакрытые journal-only gates.

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

## Что ещё не позволяет нажать Journal Submit

На 16 ноября 2026 года inference, 80+80+80 review, анализ и result-bearing
manuscript завершены. Остались:

1. similarity report и ethics determination;
2. личная reference verification всех авторов;
3. approvals точных финальных hashes статьи и презентации;
4. outside-team reproduction;
5. clean commit, GitHub CI, release archive и тег `final`.

Преподавателю пакет можно сдавать как завершённую result-bearing course
submission с честно открытыми внешними evidence items. За journal-ready пакет
его выдавать пока нельзя.

Приложенный `Team Project 2 Part 2 for Final Exam.docx` описывает отдельный
Agile-проект и в данный пакет не включается.
