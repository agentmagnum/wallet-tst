# Wallet API

REST API для работы с кошельками пользователей на FastAPI + PostgreSQL.

## Что реализовано

- `POST /api/v1/wallets/{wallet_uuid}/operation`
- `GET /api/v1/wallets/{wallet_uuid}`
- миграции Alembic
- конкурентно-безопасное изменение баланса
- Dockerfile и `docker-compose.yml`
- тесты на обычные и конкурентные сценарии

## Почему корректно работает под нагрузкой

Изменение баланса выполняется одним SQL-оператором `UPDATE ... RETURNING`.

- Пополнение делает `balance = balance + amount`.
- Списание делает `balance = balance - amount` только если `balance >= amount`.

PostgreSQL сам сериализует конфликтующие обновления одной и той же строки, а условие на баланс повторно проверяется после ожидания блокировки. Это исключает потерю обновлений и перерасход средств при параллельных запросах.

## Запуск через Docker

```bash
docker compose up --build
```

После старта:

- API: [http://localhost:8000](http://localhost:8000)
- Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)

## Запуск тестов

1. Поднять PostgreSQL:

```bash
docker compose up -d db
```

2. Установить зависимости и выполнить тесты:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:TEST_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/wallet_db"
pytest
```

## Примечание

По условию задачи endpoint создания кошелька не требуется, поэтому в тестах кошельки создаются напрямую в базе данных.
