# EventHub API

Платформа для организации и управления событиями с системой регистрации пользователей.

## Описание

EventHub API — это RESTful API для создания, управления и регистрации на события. Проект реализован на FastAPI с использованием MongoDB в качестве базы данных, Redis для кэширования и очередей задач, и TaskIQ для фоновой обработки.

## Стек технологий

- **Backend:** FastAPI (Python 3.12)
- **База данных:** MongoDB 7 (Motor — асинхронный драйвер)
- **Кэширование:** Redis 8 (redis.asyncio)
- **Очереди задач:** TaskIQ + Redis (асинхронные фоновые задачи)
- **Аутентификация:** JWT (access токен 30 мин, refresh токен 7 дней)
- **Хеширование паролей:** bcrypt
- **Контейнеризация:** Docker, Docker Compose
- **Логирование:** Loki + Promtail + Grafana
- **Формат логов:** JSON (структурированное логирование)

## Архитектура проекта

```
eventhub-api/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── admin.py          # Админские endpoint'ы
│   │   │   ├── auth.py           # Аутентификация (register, login, refresh)
│   │   │   ├── events.py         # События (CRUD, регистрации)
│   │   │   └── users.py          # Профиль пользователя
│   │   ├── api.py                # Главный роутер
│   │   └── deps.py               # Зависимости (get_current_user, require_admin)
│   ├── config_models/
│   │   ├── auth_config.py        # Настройки JWT
│   │   ├── data_base_config.py   # Настройки MongoDB
│   │   ├── event_config.py       # Настройки событий
│   │   └── redis_config.py       # Настройки Redis
│   ├── dependency_container/
│   │   ├── activation_code_deps.py
│   │   ├── event_deps.py
│   │   └── users_deps.py
│   ├── middleware/
│   │   └── logging.py            # Middleware для JSON логирования
│   ├── migrations/
│   │   ├── base.py               # База миграций
│   │   ├── runner.py             # Запуск миграций
│   │   └── versions/
│   │       └── 001_initial.py    # Первая миграция
│   ├── models/
│   │   ├── activation_code.py    # ActivationCodeDAO
│   │   ├── events.py             # EventDAO
│   │   ├── registration.py       # RegistrationDAO
│   │   └── user.py               # UserDAO
│   ├── schemas/
│   │   ├── activation_code.py    # Схемы кодов активации
│   │   ├── event.py              # Схемы событий
│   │   ├── registration.py       # Схемы регистраций
│   │   ├── token.py              # JWT токены
│   │   ├── users.py              # Схемы пользователей
│   │   └── enums/                # Enum (роли, статусы)
│   ├── services/
│   │   ├── activation_code.py    # ActivationCodeService
│   │   ├── auth.py               # AuthService (JWT, bcrypt)
│   │   ├── base.py               # BaseService (константы)
│   │   ├── cache.py              # CacheService (Redis кэш)
│   │   ├── event.py              # EventService
│   │   ├── queue.py              # QueueService (очереди задач)
│   │   └── user.py               # UserService
│   ├── tasks/
│   │   ├── __init__.py           # Экспорты
│   │   ├── broker.py             # TaskIQ брокер + startup/shutdown хуки
│   │   ├── cache.py              # Задачи инвалидации кэша
│   │   ├── cleanup.py            # Задачи очистки (delete_event_task)
│   │   ├── notifications.py      # Задачи уведомлений (email/SMS)
│   │   ├── settings.py           # Константы очередей
│   │   └── worker.py             # Точка входа воркера
│   ├── config.py                 # Конфигурация приложения
│   ├── database.py               # Подключение к MongoDB
│   ├── main.py                   # Точка входа FastAPI
│   ├── redis_client.py           # Подключение к Redis
│   └── utils/
│       └── logger.py             # Настройка логгера (JSON Formatter)
│
├── docker-compose.yml            # API + MongoDB + Redis + Worker
├── docker-compose.logging.yml    # Логирование (Loki + Promtail + Grafana)
├── Dockerfile
├── pyproject.toml                # Зависимости Poetry
├── Makefile                      # Команды для управления контейнерами
├── loki/
│   └── local-config.yml          # Конфигурация Loki
├── promtail/
│   └── config.yml                # Конфигурация Promtail
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── loki-datasource.yaml
│       └── dashboards/
│           └── loki-dashboard.yaml
└── tests/
    ├── conftest.py
    ├── core/                     # Тестовые утилиты и фабрики
    ├── mock/                     # Мок объекты
    ├── scripts/                  # Скрипты для тестов
    └── unit/                     # Юнит тесты (213 тестов)
```

## Быстрый старт

### Требования

- Docker и Docker Compose
- Python 3.12 (для локальной разработки)

### Запуск через Docker

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd eventhub-api
```

2. Создайте файл `.env`:
```env
MONGO_DB.URL=mongodb://mongodb:27017
MONGO_DB.DB_NAME=eventhub

AUTH_CONFIG.CRYPTO_SCHEMAS=bcrypt
AUTH_CONFIG.SECRET_KEY=your-secret-key-here
AUTH_CONFIG.ALGORITHM=HS256
AUTH_CONFIG.ACCESS_TOKEN_EXPIRE_TIME=30
AUTH_CONFIG.REFRESH_TOKEN_EXPIRE_TIME=7

EVENTS_CONFIG.CLEANUP_SEC=300

REDIS_CONFIG.URL=redis://redis:6379
REDIS_CONFIG.DB=0
REDIS_CONFIG.PASSWORD=
```

3. Запустите контейнеры:
```bash
docker compose up --build
```

4. Откройте Swagger UI:
```
http://localhost:8001/docs
```

### Локальная разработка

1. Установите зависимости (Poetry):
```bash
poetry install
```

2. Запустите MongoDB и Redis (через Docker):
```bash
docker run -d -p 27017:27017 --name mongodb mongo:7
docker run -d -p 6379:6379 --name redis redis:8-alpine
```

3. Создайте файл `.env`:
```env
MONGO_DB.URL=mongodb://localhost:27017
MONGO_DB.DB_NAME=eventhub
REDIS_CONFIG.URL=redis://localhost:6379
# ... остальные переменные
```

4. Запустите сервер:
```bash
uvicorn app.main:app --reload --port 8001
```

5. Запустите воркер очередей (отдельный терминал):
```bash
taskiq worker app.tasks.broker:broker
```

## API Endpoints

### Аутентификация

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/v1/auth/register` | Регистрация нового пользователя |
| POST | `/api/v1/auth/login` | Логин |
| POST | `/api/v1/auth/refresh` | Обновление пары токенов |

### Пользователи

| Метод | Endpoint | Описание | Auth |
|-------|----------|----------|------|
| GET | `/api/v1/users/me` | Получить профиль | User |
| PUT | `/api/v1/users/me` | Обновить профиль | User |
| DELETE | `/api/v1/users/me` | Удалить аккаунт | User |
| POST | `/api/v1/users/upgrade` | Повысить роль по коду | User |

### События

| Метод | Endpoint | Описание | Auth |
|-------|----------|----------|------|
| GET | `/api/v1/events` | Список событий (фильтры, пагинация) | Public |
| POST | `/api/v1/events` | Создать событие | Organizer/Admin |
| GET | `/api/v1/events/{id}` | Получить событие | Public |
| PUT | `/api/v1/events/{id}` | Обновить событие | Creator/Admin |
| DELETE | `/api/v1/events/{id}` | Удалить событие (очередь) | Creator/Admin |
| POST | `/api/v1/events/{id}/register` | Зарегистрироваться | User |
| DELETE | `/api/v1/events/{id}/register` | Отменить регистрацию | User |
| GET | `/api/v1/events/{id}/participants` | Участники | Public |
| GET | `/api/v1/events/registrations/me` | Мои регистрации | User |

### Админка

| Метод | Endpoint | Описание | Auth |
|-------|----------|----------|------|
| GET | `/api/v1/admin/users` | Список пользователей | Admin |
| PUT | `/api/v1/admin/users/{id}/ban` | Забанить | Admin |
| PUT | `/api/v1/admin/users/{id}/unban` | Разбанить | Admin |
| DELETE | `/api/v1/admin/users/{id}` | Удалить пользователя (cascade) | Admin |
| PUT | `/api/v1/admin/users/{id}/role` | Сменить роль | Admin |
| GET | `/api/v1/admin/events` | Все события | Admin |
| DELETE | `/api/v1/admin/events/{id}` | Удалить событие (очередь) | Admin |
| POST | `/api/v1/admin/activation-code` | Создать код активации | Admin |
| GET | `/api/v1/admin/activation-codes` | Список кодов | Admin |
| DELETE | `/api/v1/admin/activation-code/{id}` | Удалить код | Admin |

### Системные

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/health` | Проверка здоровья API, БД и Redis |

## Роли пользователей

- **user** — обычный пользователь (может регистрироваться на события)
- **organizer** — организатор (может создавать события)
- **admin** — администратор (полный доступ ко всем endpoint'ам)

## Коды активации

Коды активации используются для повышения роли пользователя до organizer. Администратор создаёт код, передаёт его пользователю, пользователь применяет код через endpoint `/api/v1/users/upgrade`.

## Примеры использования

### Регистрация

```bash
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "firstName": "John",
    "lastName": "Doe",
    "phoneNumber": "+1234567890"
  }'
```

### Логин

```bash
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

### Создание события

```bash
curl -X POST http://localhost:8001/api/v1/events \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Conference 2026",
    "description": "Annual tech conference",
    "location": {
      "country": "USA",
      "city": "New York",
      "address": "123 Main St"
    },
    "startDate": "2026-06-01T10:00:00Z",
    "endDate": "2026-06-01T18:00:00Z",
    "maxParticipants": 100
  }'
```

### Удаление события (через очередь)

```bash
curl -X DELETE http://localhost:8001/api/v1/events/{event_id} \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Задача выполняется асинхронно через TaskIQ воркер.

## Очереди задач (TaskIQ)

Проект использует **TaskIQ** для асинхронной обработки фоновых задач.

### Архитектура очередей

```
┌─────────────┐     ┌──────────┐     ┌──────────┐
│   FastAPI   │ ──> │   Redis  │ <── │  Worker  │
│    (API)    │     │  (Broker)│     │ (TaskIQ) │
└─────────────┘     └──────────┘     └──────────┘
```

### Задачи

| Задача | Описание | Очередь |
|--------|----------|---------|
| `delete_event_task` | Удаление события (cascade + TTL) | cleanup |
| `invalidate_event_cache_task` | Инвалидация кэша события | cache |
| `invalidate_user_cache_task` | Инвалидация кэша пользователя | cache |
| `send_registration_notification_task` | Уведомление о регистрации | notification |

### Запуск воркера

```bash
# Через Docker Compose (автоматически)
docker compose up worker

# Локально
taskiq worker app.tasks.broker:broker
```

### Мониторинг очередей

```bash
docker compose logs worker
```

## Кэширование (Redis)

Проект использует **Redis** для кэширования часто запрашиваемых данных.

### Кэшируемые данные

| Данные | TTL | Ключ |
|--------|-----|------|
| Событие | 5 мин | `event:{event_id}` |
| Пользователь | 10 мин | `user:{user_id}` |
| Список событий | 5 мин | `event:list:{filters_hash}` |
| Список пользователей | 5 мин | `user:list:{filters_hash}` |

### Инвалидация кэша

Кэш инвалидируется автоматически при:
- Обновлении данных
- Удалении данных
- Изменении роли пользователя
- Бане/разбане пользователя

## Логирование и мониторинг

Проект включает полноценную систему централизованного логирования на базе **Loki + Promtail + Grafana**.

### Архитектура логирования

```
              ┌─────────────────┐     ┌──────────┐     ┌──────────┐     ┌───────────┐
              │   FastAPI API   │ ──> │ Promtail │ ──> │   Loki   │ <── │  Grafana  │
              │   (JSON logs)   │     │  (agent) │     │ (storage)│     │   (UI)    │
              └─────────────────┘     └──────────┘     └──────────┘     └───────────┘
```

1. **Middleware** (`app/middleware/logging.py`) логирует каждый HTTP запрос в JSON формате
2. **Promtail** собирает логи из Docker контейнеров и отправляет в Loki
3. **Loki** хранит и индексирует логи
4. **Grafana** визуализирует логи (дашборды, алерты)

### Быстрый старт

**Запуск всего стека:**
```bash
make up      # Или: docker compose -f docker-compose.yml -f docker-compose.logging.yml up
```

**Просмотр логов:**
```bash
make logs    # Просмотр всех логов в реальном времени
```

**Остановка:**
```bash
make down    # Остановить и удалить контейнеры
```

### Grafana дашборд

**URL:** http://localhost:3001

**Логин/пароль:** `admin` / `admin`

**Дашборд:** Dashboards → EventHub API Logs

**Панели:**
| Панель | Описание |
|--------|----------|
| API Logs | Все запросы в реальном времени |
| 5xx Errors (5m) | Количество серверных ошибок за 5 минут |
| Total Requests (5m) | Общее количество запросов |
| Requests by Method (5m) | График по методам (GET, POST, PUT, DELETE) |
| 4xx/5xx Errors | Лог всех ошибок клиента и сервера |

### LogQL запросы (примеры)

**Все логи API:**
```logql
{service="api"}
```

**5xx ошибки:**
```logql
{service="api"} | json | status_code >= 500
```

**Медленные запросы (>500ms):**
```logql
{service="api"} | json | duration_ms > 500
```

**Запросы по методам:**
```logql
sum by (method) (count_over_time({service="api"} | json [5m]))
```

**Ошибки по эндпоинтам:**
```logql
sum by (path) (count_over_time({service="api"} | json | status_code >= 400 [1h]))
```

### Структура JSON лога

```json
{
  "timestamp": "2026-03-15 14:57:36,854",
  "level": "INFO",
  "logger": "eventhub.middleware",
  "message": "GET /health",
  "method": "GET",
  "path": "/health",
  "query": null,
  "status_code": 200,
  "duration_ms": 1.53,
  "client_ip": "172.20.0.1",
  "user_agent": "curl/8.5.0"
}
```

### Makefile команды

| Команда | Описание |
|---------|----------|
| `make up` | Запустить все контейнеры |
| `make up-d` | Запустить в фоновом режиме |
| `make down` | Остановить и удалить контейнеры |
| `make build` | Пересобрать и запустить |
| `make logs` | Смотреть логи в реальном времени |
| `make ps` | Показать статус контейнеров |
| `make clean` | Полное удаление (включая volumes) |

---

## Тестирование

Запуск тестов (pytest):

```bash
pytest --cov=app
```

### Покрытие кода

- **Отчёт в терминале:** `pytest --cov=app`
- **HTML отчёт:** `pytest --cov-report=html`
- **Allure отчёт:** `allure serve tests/reports/allure-results`

### Количество тестов: 213

## Документация

- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc
- **OpenAPI Spec:** http://localhost:8001/openapi.json

## Структура базы данных

### Коллекция `users`

```json
{
  "_id": ObjectId,
  "email": String (unique),
  "hashed_password": String,
  "first_name": String,
  "last_name": String,
  "phone_number": String,
  "role": String (user/organizer/admin),
  "is_banned": Boolean,
  "created_at": DateTime
}
```

### Коллекция `events`

```json
{
  "_id": ObjectId,
  "title": String,
  "description": String,
  "location": {
    "country": String,
    "city": String,
    "address": String,
    "lat": Number,
    "lon": Number
  },
  "start_date": DateTime,
  "end_date": DateTime,
  "max_participants": Number,
  "status": String (published/cancelled/finished),
  "recurrence": String (none/daily/weekly/monthly/yearly),
  "created_by": ObjectId,
  "created_at": DateTime,
  "deleted_at": DateTime (TTL индекс)
}
```

### Коллекция `registrations`

```json
{
  "_id": ObjectId,
  "event_id": ObjectId,
  "user_id": ObjectId,
  "registered_at": DateTime
}
```

### Коллекция `org_code` (коды активации)

```json
{
  "_id": ObjectId,
  "code": String (unique),
  "role": String,
  "is_used": Boolean,
  "created_at": DateTime,
  "activated_at": DateTime,
  "activated_by": ObjectId
}
```

## Индексы MongoDB

### users
- `email` (unique)

### events
- `startDate` (ASCENDING)
- `title` (TEXT)
- `location.city + status` (составной)
- `deleted_at` (TTL, expireAfterSeconds=0)

### registrations
- `event_id + user_id` (unique составной)
- `user_id` (ASCENDING)

### org_code
- `code` (unique)
- `activated_by` (ASCENDING)

## Безопасность

- Пароли хешируются через bcrypt
- JWT токены подписываются через HS256
- Access токен живёт 30 минут
- Refresh токен живёт 7 дней
- Забаненные пользователи не могут войти
- Cascade удаление пользователей (события + регистрации)

## Лицензия

Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0)

Copyright (c) 2026 Artem Degtyarev aka JohnyBlacksad

**Разрешено:**
- Использовать в личных и образовательных целях
- Модифицировать и форкать
- Распространять

**Запрещено:**
- Коммерческое использование
- Использование в коммерческих продуктах
- Продажа кода

**Условие:**
- При использовании нужно указать автора
- Производные работы должны быть под той же лицензией
