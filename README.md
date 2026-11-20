# plans-for-travelers

Однодневный пеший маршрут по Иванову: собственный BM25 → LLM → OSRM.
Фронтенд — React + TypeScript, API — FastAPI.

## Установка

Из корня проекта:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

В локальном `.env` заполните `ROUTERAI_API_KEY`. Настройки модели и URL —
в шаблоне. Ключ в Git не добавляется. Корпус — 30 готовых JSON в
`app/backend/data/ivanovo/`; индекс строится при старте API.
PostgreSQL, pgvector и эмбеддинги для приложения не нужны.

## Запуск

```bash
docker compose -f app/pipeline/deploy/docker-compose.yml up -d
.venv/bin/uvicorn app.backend.main:app --reload
```

Compose запускает OSRM; первый запуск скачивает карту Ивановской области и
готовит дорожные графы. LLM выбирает порядок мест, OSRM строит пеший путь.
В другом терминале запустите фронтенд (Node.js 20.19+ или 22.12+):

```bash
cd app/frontend
npm ci
npm run dev
```

Откройте http://localhost:5173. Запрос `/api` перенаправляется на порт 8000.
Документация API: http://localhost:8000/docs. Без настроенной LLM или доступного
OSRM генерация возвращает ошибку. Изображения пока заменяются заглушками интерфейса.

## Проверки

```bash
.venv/bin/python -m pytest tests -q
.venv/bin/python -m benchmark.run
```

Фронтенд: `cd app/frontend && npm run build`. Benchmark проверяет поиск без LLM.
При HTTP-прокси добавьте localhost и 127.0.0.1 в NO_PROXY для HTTP-тестов.

## Документация и работа

[Продукт](spec/product/product.md), [API](spec/tech/api-contract.md),
[архитектура](spec/tech/architecture.md), [BM25](spec/tech/rag.md),
[benchmark](benchmark/README.md).

Дарья: корпус, BM25 и benchmark. Анна: интерфейс и интеграция.
Старые компоненты векторного пайплайна не используются API; их зависимости
сохранены отдельно в `app/pipeline/requirements.txt`.
