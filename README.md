# plans-for-travelers

Однодневный пеший маршрут по Иванову: планировщик → собственный BM25 → JEV → OSRM.
Фронтенд — React + TypeScript, API — FastAPI.

## Установка

Требуются Python 3.12, Docker с Compose и Node.js 20.19+ или 22.12+.
Для запуска только benchmark Docker, Node.js и API-ключ не нужны.

Из корня проекта:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

В локальном `.env` заполните `ROUTERAI_API_KEY`. Для установки новых
зависимостей существующего окружения повторите `pip install -r requirements.txt`.
Настройки модели и URL —
в шаблоне. Ключ в Git не добавляется. Корпус — 30 готовых JSON в
`app/backend/data/ivanovo/`; индекс строится при старте API.
PostgreSQL, pgvector и эмбеддинги для приложения не нужны.

## Запуск

```bash
docker compose -f app/pipeline/deploy/docker-compose.yml up -d
.venv/bin/uvicorn app.backend.main:app --reload
```

Compose запускает OSRM; первый запуск скачивает карту Ивановской области и
готовит дорожные графы. Перед генерацией дождитесь готовности сервисов:

```bash
docker compose -f app/pipeline/deploy/docker-compose.yml ps
```

У `osrm` должен быть статус `healthy`. Планировщик задаёт ограничения, JEV
выбирает места, алгоритм маршрутизации определяет порядок, OSRM строит пеший путь.
В другом терминале запустите фронтенд (Node.js 20.19+ или 22.12+):

```bash
cd app/frontend
npm ci
npm run dev
```

Откройте http://localhost:5173. Запрос `/api` перенаправляется на порт 8000.
Документация API: http://localhost:8000/docs. Без настроенной LLM или доступного
OSRM генерация возвращает ошибку. Изображения пока заменяются заглушками интерфейса.

## Как повторить проверку BM25

После установки зависимостей, из корня проекта:

```bash
.venv/bin/python -m benchmark.run
```

Скрипт загружает 30 документов из `app/backend/data/ivanovo/` и 15 вопросов из
`benchmark/questions.json`. Для каждого вопроса выполняется один поиск по полному
тексту, без фильтрации по категориям. LLM, JEV, API и OSRM не вызываются.

По умолчанию k=30: выдача не обрезается, сохраняются все документы с положительным
баллом. В терминале выводятся **Recall@30** и **MRR@30**, усреднённые по 10 обычным
вопросам. Пять вопросов без ответа в эти метрики не входят.

Результаты каждого запуска перезаписываются:

- [bm25.md](benchmark/results/bm25.md) — вопросы, выдача с баллами и расчёты метрик.
- `benchmark/results/bm25.json` — те же данные в JSON.
- [questions.md](benchmark/questions.md) — формулировки и условия вопросов;
  `benchmark/questions.json` — вопросы и релевантные ID для скрипта.


## Проверки кода

```bash
.venv/bin/python -m pytest tests -q
```

Сборка фронтенда: `cd app/frontend && npm run build`.
При HTTP-прокси добавьте localhost и 127.0.0.1 в NO_PROXY для HTTP-тестов.

## Документация и работа

[Продукт](spec/product/product.md), [API](spec/tech/api-contract.md),
[архитектура](spec/tech/architecture.md), [BM25](spec/tech/rag.md),
[benchmark](benchmark/README.md).

Дарья: корпус, BM25 и benchmark. Анна: интерфейс и интеграция. Маршрутный граф и JEV подключены к BM25.
