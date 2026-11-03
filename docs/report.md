# Многоагентная система совместного анализа отзывов

## Отчёт по архитектуре и прототипу (этап 5-й недели)

**Тема диссертации:** *Development of a Multitask Transformer-Based Model and Web System for Joint Sentiment Analysis and AI-Generated Review Provenance Classification: A Controlled Mixed-Domain Study*

## 1. Цель и границы этапа

Цель текущего этапа — обосновать разделение задачи между несколькими ролями, определить их интерфейсы и показать работающий прототип, в котором как минимум два агента обмениваются результатами. Научная задача диссертации шире: совместная классификация тональности и provenance отзыва на основе multitask Transformer при контролируемой смешанно-доменной оценке.

В этой версии реализованы координатор и девять специализированных ролей. Результаты анализа получаются прозрачными лексическими и структурными эвристиками. Обученный Transformer, размеченный корпус и эмпирические метрики качества пока отсутствуют. Поэтому отчет подтверждает архитектуру и программный поток, но не точность будущей модели и не преимущество многоагентной или multitask-подхода.

## 2. Обоснование многоагентности

Тональность и происхождение текста требуют разных меток и признаков. Проверка языка и домена определяет, применимы ли текущие ресурсы; проверка evidence выявляет выводы без опоры на текст; отдельный reliability gate может воздержаться от ответа. Разделение ролей делает потоки данных и причины отказа наблюдаемыми и позволяет независимо менять будущие классификаторы.

Это архитектурное обоснование, а не утверждение о превосходстве агентов. Для проверки исследовательской гипотезы потребуется сравнить общий multitask encoder с отдельными моделями на одинаковых данных и splits. Совместное обучение может помочь задачам использовать общие представления, но эффект зависит от задач и данных (Caruana, 1997; Liu et al., 2019). Междоменный перенос тональности известен как отдельная трудность (Blitzer et al., 2007), а обнаружение машинно-сгенерированного текста оценивается в многоязычных, многодоменных и многомодельных условиях (Wang et al., 2024a, 2024b).

## 3. Архитектура и взаимодействие

Фиксированный граф обработки: `request_validation → preprocessing → language → context + sentiment + provenance → evidence → reliability → synthesis`. Координатор контролирует состояние и маршрутизацию; он не классифицирует текст. Вызовы сериализуются в `AgentMessage` с JSON payload и проверяются на обязательные поля. Шаги ограничены значением 12, а время запуска — 15 секундами с проверкой перед каждым новым шагом. Ошибка роли журналируется; предусмотрен один повтор.

Ключевое межагентное взаимодействие конкретно: sentiment-agent и provenance-agent передают свои отчеты evidence-agent; тот сверяет основания с исходными токенами. Reliability-agent получает language-, context-, task- и evidence-отчеты, после чего synthesis-agent собирает единый ответ, не меняя метки предшествующих ролей. Девять ролей и их контракты описаны в [спецификации](agent-specification.md), схема приведена в [архитектуре](architecture.md).

Поддерживается английский лексикон прототипа. Для неподдержанного языка система воздерживается от task-оценок. Неизвестный домен направляется к общим терминам с оговоркой. Это простая эвристика, не полноценный языковой идентификатор.

## 4. Реализация

Проект использует стандартную библиотеку Python, локальный JSON-словарь и JSONL-журналирование. Система запускается через CLI или localhost web form. Реализованы проверка входа, извлечение простых признаков, sentiment-оценка, provenance-cue оценка, проверка evidence, reliability gate, ограниченные повторы, лимиты шагов и логирование успешных и неуспешных вызовов. Provenance результат описывает только текстовые эвристики и не является доказательством авторства.

Пример запуска:

```bash
python3.12 -m review_agents --text "The delivery was quick, but the battery failed after one day." --domain electronics --json --log-dir runs
python3.12 -m review_agents --web --host 127.0.0.1 --port 8000 --log-dir runs
```

Полный тестовый запуск:

```bash
python3.12 -m unittest discover -s tests -v
```

## 5. Проверка прототипа

Автоматизированный набор содержит восемь сценариев: сквозной английский запрос и расчёт нагрузки, нейтральный доменный термин, unsupported-language abstention, пустой и чрезмерно длинный запрос, неизвестный домен, ограниченный повтор при сбое, остановка по deadline и обработчик web-формы. Последний проверяется на уровне HTTP handler с тестовым in-memory соединением; запуск настоящего сетевого сервера этим тестом не подтверждён.

Стандартный сквозной сценарий использует девять вызовов специалистов и восемь локальных tool-вызовов; LLM-вызовов нет. Согласно выбранному учёту (только tool + LLM, без маршрутизации), наибольшая доля одного агента равна 12,5%, ниже контрольного лимита 40%. Это характеристика workload конкретного запуска, не оценка качества классификации. Актуальный trace сохраняется как [JSONL демонстрации](../runs/407a0083-35dc-4744-8ef1-3b78548063b2.jsonl). Trace содержит исходный текст отзыва в сообщениях агентов; для реальных отзывов перед включением журналирования нужна политика доступа и хранения. Демонстрационный пример использует синтетический текст.

## 6. Ограничения и риски

- Лексиконы и признаки не обучены и не откалиброваны на корпусе отзывов; confidence не следует интерпретировать как калиброванную вероятность.
- Английская эвристика языка может ошибаться; русский и смешанный текст намеренно не оцениваются текущими task-классификаторами.
- Provenance detection подвержен доменному и генераторному сдвигу, редактированию текста и ложноположительным срабатываниям. Исследования детекторов подчёркивают необходимость проверки вне обучающего распределения и осторожного применения (Mitchell et al., 2023; Sadasivan et al., 2025; Liang et al., 2023).
- Deadline проверяется между шагами и не прерывает уже выполняющуюся системную операцию.
- Нагрузочное ограничение основано на вызовах инструментов/LLM; сейчас удалённых LLM нет.
- Локальный web-сервер предназначен для демонстрации, а не для публичного развертывания.

## 7. Следующие этапы

1. Выбрать лицензированные human-review источники и зафиксировать data statement, критерии включения и очистки.
2. Сгенерировать AI-отзывы несколькими документированными генераторами по фиксированным промптам; сохранить домен, тональность, генератор, версию и source ID.
3. Устранить near-duplicate leakage и зафиксировать source-grouped train/validation/test, domain-held-out и generator-held-out splits.
4. Заменить task-эвристики проверяемым multitask Transformer adapter с общей основой и двумя выходными головами; сохранить простые и single-task baselines.
5. Сравнить macro-F1 и per-class precision/recall по обеим задачам, PR-AUC для provenance, calibration и групповой bootstrap uncertainty; сообщить результаты по каждому домену и генератору.
6. Провести error analysis, проверить смещения и ограничить применение provenance-оценки исследовательским контекстом.

Подробный протокол и вопросы исследования приведены в [черновике статьи](article-draft.md). Эмпирические числа должны быть добавлены только после проведения эксперимента.

## Литература

Blitzer, J., Dredze, M., & Pereira, F. (2007). Biographies, Bollywood, boom-boxes and blenders: Domain adaptation for sentiment classification. *Proceedings of ACL 2007*, 440–447. https://aclanthology.org/P07-1056/

Caruana, R. (1997). Multitask learning. *Machine Learning, 28*, 41–75. https://doi.org/10.1023/A:1007379606734

Liang, W., Yuksekgonul, M., Mao, Y., Wu, E., & Zou, J. (2023). GPT detectors are biased against non-native English writers. *Patterns, 4*(7), 100779. https://doi.org/10.1016/j.patter.2023.100779

Liu, X., He, P., Chen, W., & Gao, J. (2019). Multi-task deep neural networks for natural language understanding. *Proceedings of ACL 2019*, 4487–4496. https://doi.org/10.18653/v1/P19-1441

Mitchell, E., Lee, Y., Khazatsky, A., Manning, C. D., & Finn, C. (2023). DetectGPT: Zero-shot machine-generated text detection using probability curvature. *Proceedings of ICML 2023, PMLR 202*, 24950–24962. https://proceedings.mlr.press/v202/mitchell23a.html

Sadasivan, V. S., Kumar, A., Balasubramanian, S., Wang, W., & Feizi, S. (2025). Can AI-generated text be reliably detected? Stress testing AI text detectors under various attacks. *Transactions on Machine Learning Research*. https://openreview.net/forum?id=00gsAZdF0t

Wang, Y., Mansurov, J., Ivanov, P., Su, J., Shelmanov, A., Tsvigun, A., Afzal, O. M., Mahmoud, T., Puccetti, G., Arnold, T., Aji, A. F., Habash, N., Gurevych, I., & Nakov, P. (2024a). M4GT-Bench: Evaluation benchmark for black-box machine-generated text detection. *Proceedings of ACL 2024*, 3964–3992. https://doi.org/10.18653/v1/2024.acl-long.218

Wang, Y., Mansurov, J., Ivanov, P., Su, J., Shelmanov, A., Tsvigun, A., Afzal, O. M., Mahmoud, T., Puccetti, G., & Arnold, T. (2024b). SemEval-2024 Task 8: Multidomain, multimodel and multilingual machine-generated text detection. *Proceedings of SemEval 2024*, 2057–2079. https://doi.org/10.18653/v1/2024.semeval-1.279
