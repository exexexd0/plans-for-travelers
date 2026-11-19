# Проверки

Созданы папки `search/`, `application/`, `api/`; тестов поведения пока нет.
Дарья добавляет проверки BM25 в `search/`, Анна — сценариев и API в остальные папки.

Из корня репозитория:

- Синтаксис Python: `python3 -m compileall -q app/backend benchmark tests`.
- Фронтенд: `cd app/frontend && npm run build`.

Качество поиска и ответов проверяется отдельно в [benchmark](../benchmark/README.md).
