# Передача работы команде перед защитой

Единая карта сдачи и подготовки находится в
`docs/FINAL_SUBMISSION_AND_DEFENSE_RU.md`; этот файл описывает распределение
ответственности.

Проект использует разрешённую преподавателем совместную AI-assisted схему.
Это единая командная разметка, а не две независимые человеческие оценки.
Ответственность распределена логически так, чтобы вклад каждого был
обязательным и сопоставимым по влиянию.

## Общий порядок

1. Aldiyar ведёт freeze. Сбор 240 test-ответов завершён и проверен; короткие и
   обрезанные ответы сохранены. Единственный retry относится к доказанному
   сбою загрузки Ollama runner до генерации и имеет incident record.
2. Codex может подготовить черновые флаги, error events и проверки целостности,
   но эти предложения не считаются независимым аннотатором.
3. Команда проверяет один blinded team-gold workbook. На каждый blind ID в
   review log указывается фактический ответственный участник, дата и статус.
   Builder заранее распределяет 240 blind ID поровну: по 80 каждому. Статус
   `pending` означает только назначение и не доказывает выполненную проверку.
4. Yerkebulan проверяет тесты, качество разметки, статистические таблицы и их
   интерпретацию.
5. Iliyas интегрирует только сгенерированные результаты в manuscript/slides и
   проводит numerical consistency audit.
6. Aldiyar выполняет финальный provenance/release audit. После общего одобрения
   внешний человек воспроизводит Results по README; только потом создаётся тег
   `final`.

## Aldiyar Zhaksylyk

- Отвечает за Mac/Ollama, exact model digests, frozen protocol, request controls,
  receipts, ambiguous-timeout rule и отсутствие quality-based regeneration.
- Проверяет, что AI-assisted provenance раскрыт и нигде не выдан за независимую
  разметку.
- На защите показывает происхождение результата от raw receipt до таблицы.

## Yerkebulan Rakhymbay

- Отвечает за tests, label quality control и статистическую проверку.
- Проверяет primary endpoint, Friedman permutation test, Kendall's W, Pratt
  pairwise tests, Holm correction, bootstrap intervals и различие H1/H2 versus
  H3/H4.
- На защите объясняет, почему joint-team gold не позволяет оценить
  inter-annotator reliability.

## Iliyas Aitzhan

- Отвечает за интеграцию team gold и generated results.
- Проверяет совпадение чисел в tables, figures, manuscript и slides, journal fit,
  declarations, references и ACM template compliance.
- На защите объясняет ограничения, reporting chain и итоговую визуализацию.

## Команды

```bash
.venv/bin/python scripts/validate_run.py runs/final_test_v2 --expected 240
.venv/bin/python scripts/validate_annotation_workbook.py \
  annotations/team_gold/final_test_v2__team_gold.xlsx --expected-responses 240
.venv/bin/python scripts/analyze_final.py
.venv/bin/python scripts/release_gate.py
```

Пошаговая инструкция по проверке назначенных 80 blind ID находится в
`docs/TEAM_REVIEW_INSTRUCTIONS_RU.md`. AI-черновик не завершает этот этап за
участника: имя, время и `approved` в review log ставятся только после реальной
проверки человеком. Текущий 22-item QC sample не применён к Excel.

## Что взять на защиту

- Aldiyar: freeze manifest, authorization disclosure, model/environment hashes,
  request accounting, provenance chain и reproduction command.
- Yerkebulan: CI/test run, label-QA notes, statistical tables/figure и analysis
  review record.
- Iliyas: team-gold integration record, manuscript consistency audit,
  journal/template record и final slides.

Каждый участник должен уметь объяснить research question, design, главный
результат, основное ограничение и почему данные не были сфабрикованы.
