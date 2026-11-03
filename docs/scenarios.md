# Сценарии демонстрации и оценки

Сценарии A4 и экзамена теперь представлены исполняемыми тестами. Команда запуска:

```bash
python3.12 -m unittest discover -s tests -v
```

Подходит любой Python 3.10+. Это покрытие прототипа; оно не заменяет экспериментальную оценку качества multitask-модели.

## Демонстрация

```bash
python3.12 -m review_agents --text "The delivery was quick, but the battery failed after one day." --domain electronics --show-trace --log-dir runs
```

Ожидается: запрос проходит validation, preprocessing и language gate; sentiment возвращает негативное слово `failed`, provenance оценивается отдельно, evidence-check подтверждает grounding, reliability указывает низкую опору эвристики provenance. Итог включает девять вызовов специалистов, восемь tool-вызовов, workload и caveats. В текущем полном сценарии максимум — 12,5% всех LLM/tool-вызовов на одного агента.

## Набор сценариев для Ассайнмента 4 (5 основных)

| ID / тест | Вход | Проверяемый результат |
|---|---|---|
| A4-1 `test_english_end_to_end_and_tool_balance` | Английский electronics-отзыв, позитивное и негативное основания | Все роли завершены; evidence grounded; workload не превышает 40%. |
| A4-2 `test_neutral_domain_term_is_context_only` | `The battery failed.` | `battery` остаётся контекстным термином, не получает позитивную полярность. |
| A4-3 `test_unsupported_language_abstains` | Русский отзыв hotel-домена | Sentiment и provenance воздерживаются, reliability возвращает `abstain`. |
| A4-4 `test_invalid_inputs_are_rejected_by_request_agent` | Пустой и превышающий 5000 символов текст | Отказ с понятной причиной до предметного анализа. |
| A4-5 `test_unknown_domain_uses_general_terms_with_caveat` | Известный язык, неизвестный домен | Используется общий словарь, результат получает caveat. |

## Проверки надёжности и интерфейса

| Тест | Проверяемый результат |
|---|---|
| `test_agent_failures_are_bounded_and_logged` | После двух попыток сбой остановлен и записан. |
| `test_time_limit_stops_before_next_agent` | Новый шаг не начинается после deadline. |
| `test_local_web_form_returns_analysis` | GET показывает форму; POST анализирует запрос, отображает результат и сохраняет trace. |

## Сохранённая демонстрационная трасса

Актуальный JSONL-пример с типовым запросом: [`407a0083-35dc-4744-8ef1-3b78548063b2.jsonl`](../runs/407a0083-35dc-4744-8ef1-3b78548063b2.jsonl). Он создан командой CLI после прохождения тестового набора и содержит полный девятиагентный trace, восемь tool-вызовов и workload summary.

## Экзаменационные сценарии (6+)

Текущие тесты исполняют 8 сценариев и покрывают основные взаимодействия/отказы. Для полноценной оценки будущей модели добавьте размеченные кейсы для смешанной тональности, unknown generator, domain-held-out переноса, короткого и длинного текста, редактированного AI-текста и классового дисбаланса. Ожидаемые научные метки должны быть получены из эталонной разметки, а не из прототипных эвристик.
