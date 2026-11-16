# Финальная сдача и защита: единая инструкция

Актуально на 16 ноября 2026 года (Asia/Almaty). Этот файл — основной
операционный документ команды. Исторические Assignment 1–4 сохранены как
provenance и не используются как отдельные части финальной статьи.

## Короткий статус

- **Сбор и review завершены:** 240 из 240 ответов сохранены; workbook и
  240-строчный review log валидны и привязаны к исходным данным.
- **Финальный анализ рассчитан:** 60 полных paired blocks; H1 и H2 поддержаны,
  H3 и H4 не поддержаны. KazLLM показал наименьший mean response rate: 1.20
  primary events на 100 слов.
- **Статья и cover letter обновлены реальными Results:** прежние pre-results
  заглушки удалены; все числа берутся из `results/derived/final_test_v2/`.
- **Презентация обновлена реальными Results:** готовы 10-слайдовые PDF и
  редактируемый PPTX; отдельное team presentation review ещё не записано.
- **Journal release пока закрыт:** отсутствуют внешние similarity/ethics,
  личная reference verification, финальные author/presentation approvals,
  outside-team reproduction и clean release commit/tag.

## Что сдаётся по критерию

| № | Обязательный объект | Канонический файл / ссылка | Текущий статус |
|---:|---|---|---|
| 1 | Manuscript в шаблоне выбранного журнала | `deliverables/Kazakh_LLM_Study_ACM_Submission.docx` | Result-bearing версия готова и проходит автоматическую проверку |
| 2 | Journal Fit Statement | `docs/JOURNAL_FIT_STATEMENT.md` | Готов; источники должны быть лично прочитаны авторами |
| 3 | Одностраничный cover letter | `deliverables/Cover_Letter_TALLIP.docx` | Result-bearing письмо готово; внешняя отправка остаётся gated |
| 4 | Reproducibility package | GitHub repository и release/tag `final` | Данные и анализ готовы; clean release/tag пока не создан |
| 5 | Presentation slides | `output/pdf/Kazakh_LLM_Defense_Deck.pdf`; `deliverables/Kazakh_LLM_Defense_Deck.pptx` | 10 result-bearing слайдов; PDF и editable PPTX готовы |
| 6 | Submission Readiness Checklist | `docs/RELEASE_CHECKLIST.md` | Технические/results пункты закрыты; внешние подтверждения открыты |

Файл `Team Project 2 Part 2 for Final Exam.docx` относится к другому Agile-
заданию и в пакет этого исследования не входит.

## Что сдавать преподавателю

1. `deliverables/Kazakh_LLM_Study_ACM_Submission.docx`;
2. `deliverables/Cover_Letter_TALLIP.docx`;
3. `output/pdf/Kazakh_LLM_Defense_Deck.pdf`;
   при необходимости редактирования — `deliverables/Kazakh_LLM_Defense_Deck.pptx`;
4. `docs/JOURNAL_FIT_STATEMENT.md` и `docs/RELEASE_CHECKLIST.md`;
5. ссылку на `https://github.com/qsheker/kazakh-llm-error-study`;
6. финальный ZIP репозитория после clean commit, без model binaries, private
   key, `.venv` и секретов.

Для немедленной сдачи преподавателю собран
`output/packages/Kazakh_LLM_Final_Course_Submission.zip`. Он содержит основные
документы, PDF/PPTX, проверенную team-gold разметку и generated Results вместе с
SHA-256 manifest. Это course-submission ZIP, а не journal release archive.

Это result-bearing course submission. Не отправлять пакет в журнал и не
создавать release/tag `final`, пока `scripts/release_gate.py` не вернёт
`ready: true`.

## Что обязательно завершить перед финальной сдачей

### 1. Зафиксировать завершённую командную разметку

Workbook содержит 240 approved response records и 855 событий; review log
распределён 80/80/80. В provenance должно оставаться точное описание:
AI-assisted drafts, подтверждение назначенных reviewers и внесение записей
координатором. Нельзя переименовывать этот процесс в независимую human
annotation или заявлять inter-annotator reliability.

### 2. Перегенерировать и проверить Results при любом изменении workbook

```bash
.venv/bin/python scripts/validate_annotation_workbook.py \
  annotations/team_gold/final_test_v2__team_gold.xlsx --expected-responses 240
.venv/bin/python scripts/analyze_final.py --output /path/to/new-empty-output-dir
```

Валидатор сейчас проходит. Анализ намеренно отказывается перезаписывать уже
замороженный `results/derived/final_test_v2/`, поэтому контрольный повторный
запуск делается только в новом пустом каталоге, после чего его outputs и hashes
сверяются с каноническими. После любого изменения annotation inputs анализ и
документы нужно собрать заново; вручную менять число только в статье нельзя.

### 3. Финальная числовая сверка

Ильяс сверяет abstract, Results, Discussion, Conclusion и слайды с generated
outputs. Еркебулан проверяет test names, adjusted p-values, направления
contrasts и интервалы. Алдияр проверяет цепочку input hashes и release diff.
Основные значения: Friedman 51.16, p=0.00001, W=0.284; Llama minus KazLLM
2.53 [1.14, 3.94], Holm p=0.01134; hybrid-minus-Latin F1 interval
[-0.090, 0.198].

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
   generated table/figure → manuscript/slide`. Если числа нет в generated
   evidence, честный ответ — «не проверено», а не догадка.

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
analysis_check_dir="$(mktemp -d)"
.venv/bin/python scripts/analyze_final.py --output "$analysis_check_dir"
.venv/bin/python scripts/release_gate.py
```

Нормальный текущий результат: оба валидатора и контрольный анализ в новом
пустом каталоге проходят, а release gate сообщает `ready: false` и перечисляет
только реальные незакрытые evidence и release checks. Нормальный journal-final
результат: все проверки завершаются успешно, а release gate сообщает
`ready: true`.
