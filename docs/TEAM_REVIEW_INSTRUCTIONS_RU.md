# Проверка team-gold разметки

Это обязательный человеческий этап финального маршрута из
`docs/FINAL_SUBMISSION_AND_DEFENSE_RU.md`. По состоянию на 16 ноября 2026 года
workbook validation останавливается на пустых полях; назначения 80/80/80 не
равны завершённым reviews.

## Что уже подготовлено

- `annotations/team_gold/final_test_v2__team_gold.xlsx` — одна общая blinded
  книга на 240 ответов. Названия моделей скрыты.
- `annotations/team_gold/team_review_log.csv` — назначения: Aldiyar,
  Yerkebulan и Iliyas получают ровно по 80 blind ID.
- `annotations/team_gold/ai_draft_provenance.json` — provenance 22-item QC
  sample. Он не применён к Excel; совпадающие before/after hashes это
  подтверждают. Файл можно использовать только как подсказку для совпадающего
  blind ID, но не как решение человека.

## Что обязан сделать каждый участник

1. В `team_review_log.csv` отфильтровать строки по своему имени в
   `assigned_reviewer`. Проверить, что строк ровно 80.
2. Для каждого `blind_id` найти строку на листе **Responses**. Прочитать prompt,
   полный response и reference/constraint card; модель угадывать нельзя.
3. Проверить пять response-level полей: `refusal`, `off_task`,
   `requirement_missing`, `repetition`, `fabricated_specificity`. Допустимый
   финальный ответ — только `yes` или `no`. Если требование пропущено,
   перечислить его в `missing_requirements`.
4. На листе **Error events** проверить каждое событие этого `blind_id` и при
   необходимости удалить, исправить или добавить его. Фрагмент должен дословно
   совпадать с response, offsets и token indices — указывать именно этот
   фрагмент, correction должна реально отличаться и исправлять одну ошибку.
5. У каждого сохранённого event заменить `needs_adjudication` на `no` только
   после принятого решения. В финальной книге не должно остаться ни одного
   `yes` или пустого решения у существующего event.
6. В `team_review_log.csv` только после фактической проверки заполнить:
   `review_status=approved`, `reviewer` своим настоящим именем и `reviewed_utc`
   реальным временем UTC в ISO 8601. `ai_assistance=yes` ставится только если
   участник действительно открыл AI draft именно для этого blind ID; иначе
   ставится `no`. В `notes` кратко записываются спорные решения. Нельзя заранее
   массово отметить строки approved.

## Разделение ответственности

- **Aldiyar Zhaksylyk:** свои 80 blind ID плюс provenance, receipts и финальный
  release audit.
- **Yerkebulan Rakhymbay:** свои 80 blind ID плюс label-QA, тесты и проверка
  статистических выводов.
- **Iliyas Aitzhan:** свои 80 blind ID плюс интеграция generated results,
  числовая согласованность manuscript/slides и финальный QA.

## Проверка после всех 240 человеческих решений

```bash
.venv/bin/python scripts/validate_annotation_workbook.py \
  annotations/team_gold/final_test_v2__team_gold.xlsx --expected-responses 240
.venv/bin/python scripts/analyze_final.py
.venv/bin/python scripts/release_gate.py
```

`analyze_final.py` должен оставаться заблокирован, пока хотя бы одна строка
review log не завершена или хотя бы одно событие требует adjudication. Это
защита от выдачи AI-черновика за итоговую человеческую разметку.
