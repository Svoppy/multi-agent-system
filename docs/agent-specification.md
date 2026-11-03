# Спецификация агентов

Система состоит из координатора и девяти специалистов. Все роли передают `AgentMessage` JSON. Одна роль владеет одной функцией; у каждого специалиста не более пяти инструментов. Каждый agent payload проверяется на наличие обязательных ключей роли.

| Роль | Вход | Выход | Инструменты (0–5) | Условие завершения |
|---|---|---|---|---|
| **Координатор** | Задача и `RunState` | Следующий маршрут, финальный результат или контролируемая ошибка | Фиксированный граф; валидатор envelope; журнал событий | Сценарий завершён либо остановлен за 12 шагов/15 секунд; предметную обработку не выполняет |
| **1. Валидация запроса** | `review`, `domain` | `valid`, `errors[]` | `validate_request` | Возвращает `valid=true` или конкретную причину отказа |
| **2. Предобработка** | Валидный `review` | `tokens[]`, `features{}` | `text_features` | Возвращены токены и счётчики в JSON |
| **3. Языковой агент** | `tokens[]` | Язык, уверенность heuristic, supported flag | `detect_language` | Язык распознан как English-supported или явно неизвестный/unsupported |
| **4. Контекст домена** | Домен из state, `tokens[]` | Найденные доменные термины, coverage, версия словаря | `load_domain_lexicon` | Есть контекстный отчёт; неизвестный домен указан как `general_only` |
| **5. Sentiment** | `tokens[]`, language report | Полярность/`not_assessed`, score, heuristic confidence, evidence | `load_domain_lexicon` | Выдана полярность только при поддержанном языке |
| **6. Provenance** | `tokens[]`, `features{}`, language report | Оценка текстовых сигналов/`not_assessed`, причины, caveat | `inspect_provenance_cues` | Сигналы возвращены или оценка отозвана для неподдержанного языка |
| **7. Evidence-check** | Источник, sentiment и provenance reports | `grounded`, неподтверждённые слова, checks | `check_evidence_against_source` | Каждое процитированное основание сопоставлено с исходными токенами |
| **8. Reliability gate** | Language, context, sentiment, provenance, evidence reports | Решение `ready_within_prototype_scope`, `review_with_caveats`, `manual_review` или `abstain` | `apply_reliability_policy` | Возвращено decision и список причин |
| **9. Синтез** | Все отчёты предыдущих ролей | Итоговый JSON, ограничения и workload summary | Нет | Обязательные разделы собраны без смены меток предыдущих агентов |

## Контракт сообщений

```json
{
  "schema_version": "1.0",
  "run_id": "uuid",
  "message_id": "uuid",
  "sender": "sentiment_agent",
  "recipient": "orchestrator",
  "message_type": "analysis_result",
  "status": "complete",
  "payload": {
    "label": "negative",
    "score": -1.5,
    "confidence": 0.62,
    "method": "transparent_prototype_lexicon",
    "validated_model": false
  }
}
```

Envelope проверяет наличие непустых строк `run_id`, `message_id`, `sender`, `recipient`, `message_type`, а также объектный тип payload. Дополнительно у каждой роли выполняется проверка обязательных ключей input/output. Это лёгкая проверка контрактов, не полная JSON Schema-валидация типов и диапазонов.

### Пример взаимодействия

Для `The delivery was quick, but the battery failed after one day.` языковой агент подтверждает, что английские лексиконы применимы. Затем sentiment сообщает отрицательное evidence `failed`, а provenance отдельно анализирует стилистические признаки. Evidence-agent получает оба отчёта и сверяет их с исходным текстом. Reliability-agent объединяет язык, поддержку домена, уверенность и grounded-check; synthesis-agent формирует конечный JSON с оговорками. Результат доступен в [демонстрационном trace](../runs/).

Уверенность демонстрационных правил не является откалиброванной вероятностью. Метка provenance описывает результат heuristic classifier, а не устанавливает фактического автора.
