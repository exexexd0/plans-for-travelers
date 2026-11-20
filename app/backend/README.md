# Изолированный поиск BM25

Python 3.12+. BM25 реализован самостоятельно; для лемматизации используется
`pymorphy3`. Сервер и LLM для изолированного поиска не требуются.
API использует тот же BM25 для однодневного маршрута; установка и запуск —
в корневом README.
Из корня репозитория:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r app/backend/requirements.txt
python -m unittest discover -s tests -v
python -m app.backend.infrastructure.search --corpus app/backend/data/ivanovo --query "музей" --city Иваново --limit 3
```

Поиск использует готовые карточки Иванова. CLI печатает JSON с ID, текстами и баллами.
Пример A/B/C из презентации проверяется в `tests/search/test_bm25.py`.

Для своего нормализованного корпуса передай его путь в `--corpus`.
Дополнительно: `--city`, повторяемые `--category` и `--exclude-id`, `--k1`, `--b`.
`--limit` задаётся явно; это не согласованное k итогового benchmark.

- `domain/models.py`: Place, SearchDocument (подборка) и SearchHit.
- `application/ports.py`: SearchPort — контракт для интеграции.
- `infrastructure/search/bm25.py`: индекс и ранжирование.
- `infrastructure/search/preprocessing.py`: общая обработка документов и запросов.
- `infrastructure/corpus/loader.py`: чтение и проверка JSON.

Формула, формат корпуса и ограничения: [rag.md](../../spec/tech/rag.md).
Поисковый benchmark подготовлен; ответы LLM для benchmark пока не получены.

## Корпус и вопросы

30 документов разных категорий с 336 местами лежат в `data/ivanovo/`.
Загрузчик читает вложенные места; поиск ранжирует подборки. [Вопросы и эталоны](../../benchmark/questions.md) утверждены пользователем. Лемматизация объединяет словоформы документов и запросов;
служебные стоп-слова удаляются после лемматизации; отрицания и «без» сохраняются. Имена собственные и неоднозначные слова могут разбираться
неверно. После обновления предобработки индекс нужно построить заново.

Для запуска используются готовые 30 подборок; пересборка исходной выгрузки не нужна.

## Поисковый benchmark

Из корня проекта, в активированной .venv: `python -m benchmark.run`.
Он использует тот же BM25 без сервера и LLM; отчёт — в `benchmark/results/search.md`.
Метрики поиска не заменяют проверку ответов модели.

`pipeline_adapter.py` соединяет BM25, LlmSelector и OSRM.
Для API нужен корневой requirements.txt. Векторная база не используется.
