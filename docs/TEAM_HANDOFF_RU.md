# Передача работы команде перед защитой

Этот файл разделяет интеллектуальную ответственность, а не имитирует равное
число коммитов. Пока действие не выполнено лично указанным участником, оно не
считается завершённым.

## Общий порядок

1. Все трое проверяют 60 test-карточек и список допустимых латинских фрагментов.
2. Каждый лично создаёт свой sign-off. После трёх подписей Aldiyar замораживает
   протокол.
3. Aldiyar один раз собирает 240 test-ответов и сохраняет все неудачные,
   короткие и обрезанные ответы без выборочной перегенерации.
4. Yerkebulan и Iliyas независимо заполняют разные blinded workbooks. Им нельзя
   смотреть ключ моделей, файл другого аннотатора или automatic detector output.
5. Aldiyar объединяет разметки и выносит разногласия на adjudication до открытия
   ключа моделей.
6. Yerkebulan проверяет статистические таблицы и их интерпретацию. Iliyas
   переносит только сгенерированные результаты в manuscript и slides и проводит
   numerical consistency audit.
7. Все трое читают итоговую версию и подтверждают её; внешний человек повторяет
   Results по README. Только после этого создаётся тег `final`.

## Aldiyar Zhaksylyk

- Лично проверяет freeze bundle и создаёт `protocol/signoffs/aldiyar.json`.
- Отвечает за Mac/Ollama, exact model digests, request controls, receipts,
  ambiguous-timeout rule и отсутствие quality-based regeneration.
- После независимых разметок проводит blinded adjudication с письменной причиной
  каждого решения.
- На защите показывает происхождение любого результата от receipt до таблицы.

## Yerkebulan Rakhymbay

- Лично проверяет freeze bundle и создаёт `protocol/signoffs/yerkebulan.json`.
- Проходит training calibration, затем blinded qualification. Порог нельзя
  считать пройденным до генерации agreement report.
- Самостоятельно заполняет полный Rater 1 workbook.
- Проверяет tests, primary endpoint, Friedman permutation test, Kendall's W,
  Pratt pairwise tests, Holm correction, bootstrap intervals и H1/H2 versus
  H3/H4 interpretation.

## Iliyas Aitzhan

- Лично проверяет freeze bundle и создаёт `protocol/signoffs/iliyas.json`.
- Проходит training calibration, затем blinded qualification независимо от
  Yerkebulan.
- Самостоятельно заполняет полный Rater 2 workbook.
- После разморозки результатов интегрирует generated tables/figures в manuscript
  и slides, проверяет совпадение каждого числа, journal fit, declarations,
  references и ACM template compliance.

## Команды без подмены человеческой работы

```bash
# каждый запускает только свою команду из protocol/signoffs/README.md
.venv/bin/python scripts/freeze_protocol.py
.venv/bin/python scripts/collect.py --dataset test --preflight
.venv/bin/python scripts/collect.py --dataset test --send --run-id final_test_v2

# после получения двух заполненных файлов
.venv/bin/python scripts/validate_annotation_workbook.py annotations/rater_1/final_test_v2__rater_1.xlsx --expected-responses 240
.venv/bin/python scripts/validate_annotation_workbook.py annotations/rater_2/final_test_v2__rater_2.xlsx --expected-responses 240
.venv/bin/python scripts/prepare_adjudication.py annotations/rater_1/final_test_v2__rater_1.xlsx annotations/rater_2/final_test_v2__rater_2.xlsx --blinded-manifest annotations/final_test_v2__blinded_manifest.json --expected-responses 240
.venv/bin/python scripts/analyze_final.py
.venv/bin/python scripts/release_gate.py
```

## Что взять на защиту

- Aldiyar: freeze manifest, model/environment hashes, request accounting,
  adjudication log, reproduction command.
- Yerkebulan: immutable Rater 1 hash, CI/test run, agreement report, statistical
  tables and figure, analysis review notes.
- Iliyas: immutable Rater 2 hash, final manuscript checklist, number-consistency
  audit, journal/template record, final slides.

Каждый участник всё равно должен уметь объяснить research question, design,
главный результат, основное ограничение и почему данные не были сфабрикованы.
