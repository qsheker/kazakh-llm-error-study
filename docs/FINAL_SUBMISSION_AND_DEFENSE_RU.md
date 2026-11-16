# Финальная сдача и защита: единая инструкция

Актуально на 16 ноября 2026 года (Asia/Almaty). Этот файл — основной
операционный документ команды. Исторические Assignment 1–4 сохранены как
provenance и не используются как отдельные части финальной статьи.

## Короткий статус

- **Сбор данных завершён:** 240 из 240 ответов сохранены и валидированы.
- **Инженерная часть готова:** протокол заморожен, модели и окружение
  зафиксированы, тесты и публичный CI проходят.
- **Лингвистический результат ещё не готов:** в blinded workbook остаются
  пустые human-review поля, поэтому статистика и ranking моделей отсутствуют.
- **Пакет документов собран как pre-results review package:** его можно
  показать преподавателю для проверки процесса, но нельзя называть полной
  result-bearing submission или отправлять в журнал.

## Что сдаётся по критерию

| № | Обязательный объект | Канонический файл / ссылка | Текущий статус |
|---:|---|---|---|
| 1 | Manuscript в шаблоне выбранного журнала | `deliverables/Kazakh_LLM_Study_ACM_Submission.docx` | Контролируемый draft; нужны реальные Results |
| 2 | Journal Fit Statement | `docs/JOURNAL_FIT_STATEMENT.md` | Готов; источники должны быть лично прочитаны авторами |
| 3 | Одностраничный cover letter | `deliverables/Cover_Letter_TALLIP.docx` | Draft; красное предупреждение удаляется только после release gate |
| 4 | Reproducibility package | GitHub repository и release/tag `final` | Репозиторий готов; `final` пока запрещён |
| 5 | Presentation slides PDF | `output/pdf/Kazakh_LLM_Defense_Deck.pdf` | 10 слайдов; нужны реальные result slides |
| 6 | Submission Readiness Checklist | `docs/RELEASE_CHECKLIST.md` | Заполнен честно; незакрытые пункты оставлены пустыми |

Файл `Team Project 2 Part 2 for Final Exam.docx` относится к другому Agile-
заданию и в пакет этого исследования не входит.

## Что можно отправить преподавателю прямо сейчас

Отправлять только с формулировкой **pre-results review package**:

1. `output/packages/Kazakh_LLM_PreResults_Review_Package.zip`;
2. ссылку на `https://github.com/qsheker/kazakh-llm-error-study`;
3. `deliverables/Kazakh_LLM_Study_ACM_Submission.docx`;
4. `output/pdf/Kazakh_LLM_Defense_Deck.pdf`;
5. пояснение: «240 генераций завершены; human review 240 blinded responses и
   статистическая интеграция ещё выполняются; числовые результаты не
   сфабрикованы».

Не отправлять cover letter в редакцию и не создавать тег `final` на этом
этапе.

## Что обязательно завершить перед финальной сдачей

### 1. Командная разметка

Каждый участник проверяет назначенные 80 blind ID в
`annotations/team_gold/final_test_v2__team_gold.xlsx` и заполняет только после
реального чтения ответа и reference card. Подробные правила находятся в
`docs/TEAM_REVIEW_INSTRUCTIONS_RU.md`.

- Aldiyar: 80 строк + provenance/release audit.
- Yerkebulan: 80 строк + label-QA, tests, statistics.
- Iliyas: 80 строк + integration, numerical consistency, final QA.

Открыть workbook в Excel/LibreOffice, а `team_review_log.csv` — в отдельном
окне. Нельзя массово проставлять `approved` заранее. AI draft — подсказка, а не
человеческое решение.

### 2. Генерация результатов

После 240 реальных review:

```bash
.venv/bin/python scripts/validate_annotation_workbook.py \
  annotations/team_gold/final_test_v2__team_gold.xlsx --expected-responses 240
.venv/bin/python scripts/analyze_final.py
```

Ожидаются `summary.json`, detector metrics, sensitivity analysis,
model-by-task analysis, input hashes, таблицы и primary figure. Если команда
падает, исправляется источник ошибки; нельзя вручную сочинять число в статье.

### 3. Интеграция без расхождения чисел

Ильяс переносит только сгенерированные значения в abstract, Results,
Discussion, Conclusion и слайды. Еркебулан сверяет статистические выводы и
границы интервалов. Алдияр проверяет, что каждое число ведёт к immutable input
и generated output. Все три участника подписывают один и тот же хэш версии.

### 4. Человеческие и институциональные подтверждения

Нужны реальные, а не заполненные за других документы:

- отчёт university similarity checker;
- ethics determination / подтверждение, что отдельное approval не требуется;
- личная проверка references каждым автором;
- all-author approval и presentation review;
- воспроизведение main Results человеком вне команды;
- при наличии — письменное подтверждение разрешения команды из трёх человек.

Шаблоны в `evidence/templates/` показывают структуру записи, но сами не
являются доказательством.

### 5. Финальный release

```bash
.venv/bin/python scripts/release_gate.py
```

Только когда команда возвращает `ready: true`, обновить документы и PDF,
собрать release archive, проверить отсутствие secrets/private model key,
запушить clean commit и создать GitHub release/tag `final`.

## Как подготовиться к защите

### Общая 10-минутная репетиция

| Время | Спикер | Содержание |
|---|---|---|
| 0:00–3:20 | Aldiyar | Problem, RQ, 60 prompts × 4 models, frozen artifacts, Mac/Ollama execution, receipts, retry rule |
| 3:20–6:40 | Yerkebulan | Annotation outcome, label QA, Friedman/Kendall/Pratt-Holm/bootstrap, main result table/figure |
| 6:40–10:00 | Iliyas | Interpretation, reviewed examples, limitations, journal fit, reproducibility, conclusion |

Каждый обязан уметь самостоятельно объяснить весь study, потому что 23 балла
за individual defence ставятся отдельно. Владение своим блоком не освобождает
от вопросов по чужому.

### Пять ответов, которые должны звучать без подсказки

1. **Contribution:** reproducible paired comparison of four exact local model
   configurations on a balanced Kazakh prompt resource with auditable error
   events and immutable receipts.
2. **Почему 240:** 60 одинаковых prompts × 4 models; prompt — блок paired
   comparison, а не 240 независимых наблюдений.
3. **Почему baseline fair:** одинаковые request controls и prompt set, но
   сравниваются полные configurations; разные parameter counts/templates не
   позволяют утверждать чистый causal effect архитектуры.
4. **Главное ограничение:** purposeful 60-prompt sample, один quantized artifact
   на family, один Mac/Ollama environment и joint gold без независимой
   inter-annotator reliability.
5. **Откуда число:** показать путь `receipt → blinded review → frozen workbook →
   generated table/figure → manuscript/slide`. До генерации конкретного числа
   честный ответ — «result pending», а не догадка.

### Минимальный rehearsal gate

- Две полные репетиции с таймером и одна запись на видео.
- Каждый отвечает минимум на пять hostile questions из
  `docs/DEFENSE_PLAN.md`.
- Каждый показывает на ноутбуке один raw receipt, model digest, review row и
  generated result output.
- Все произносимые числа сверены с generated outputs.
- Отдельно отрепетирован вопрос про Gemma E13: первый вызов не создал response,
  runner-load incident сохранён, retry использовал идентичный payload и не был
  quality-based regeneration.

## Что взять на защиту

- ноутбук и зарядку;
- локальную копию репозитория на clean commit;
- PDF-слайды офлайн;
- открытые вкладки/файлы: `completion.json`, один receipt,
  `config/model_artifacts.json`, generated summary/figure, checklist;
- резервную копию PDF и ZIP на флешке или облаке;
- короткий список точных команд демонстрации без повторного запуска моделей.

Не запускайте 240 inference-запросов на защите. Показывайте сохранённые
immutable receipts и короткую валидацию: это быстрее и воспроизводимее.

## Финальная команда проверки

```bash
.venv/bin/python scripts/validate_run.py runs/final_test_v2 --expected 240
.venv/bin/python scripts/validate_annotation_workbook.py \
  annotations/team_gold/final_test_v2__team_gold.xlsx --expected-responses 240
.venv/bin/python scripts/analyze_final.py
.venv/bin/python scripts/release_gate.py
```

Нормальный текущий результат: первая команда проходит, вторая останавливается
на пустой human label, а release gate сообщает `ready: false`. Нормальный
финальный результат: все четыре команды завершаются успешно, а release gate
сообщает `ready: true`.
