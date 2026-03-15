# EventHub API

Платформа для организации и управления событиями с системой регистрации пользователей.

## Описание

EventHub API — это RESTful API для создания, управления и регистрации на события. Проект реализован на FastAPI с использованием MongoDB в качестве базы данных.

## Стек технологий

- **Backend:** FastAPI (Python 3.12)
- **База данных:** MongoDB 7 (Motor — асинхронный драйвер)
- **Аутентификация:** JWT (access токен 30 мин, refresh токен 7 дней)
- **Хеширование паролей:** bcrypt
- **Контейнеризация:** Docker, Docker Compose

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
│   │   └── event_config.py       # Настройки событий
│   ├── dependency_container/
│   │   ├── activation_code_deps.py
│   │   ├── event_deps.py
│   │   └── users_deps.py
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
│   │   ├── event.py              # EventService
│   │   └── user.py               # UserService
│   ├── config.py                 # Конфигурация приложения
│   ├── database.py               # Подключение к MongoDB
│   └── main.py                   # Точка входа
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
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

2. Запустите контейнеры:
```bash
docker compose up --build
```

3. Откройте Swagger UI:
```
http://localhost:8001/docs
```

### Локальная разработка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте файл `.env`:
```env
MONGO_DB.URL=mongodb://localhost:27017
MONGO_DB.DB_NAME=eventhub

AUTH_CONFIG.CRYPTO_SCHEMAS=bcrypt
AUTH_CONFIG.SECRET_KEY=your-secret-key-here
AUTH_CONFIG.ALGORITHM=HS256
AUTH_CONFIG.ACCESS_TOKEN_EXPIRE_TIME=30
AUTH_CONFIG.REFRESH_TOKEN_EXPIRE_TIME=7

EVENTS_CONFIG.CLEANUP_SEC=300
```

3. Запустите MongoDB (локально или через Docker):
```bash
docker run -d -p 27017:27017 --name mongodb mongo:7
```

4. Запустите сервер:
```bash
uvicorn app.main:app --reload --port 8001
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
| DELETE | `/api/v1/events/{id}` | Удалить событие | Creator/Admin |
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
| DELETE | `/api/v1/admin/events/{id}` | Удалить событие | Admin |
| POST | `/api/v1/admin/activation-code` | Создать код активации | Admin |
| GET | `/api/v1/admin/activation-codes` | Список кодов | Admin |
| DELETE | `/api/v1/admin/activation-code/{id}` | Удалить код | Admin |

### Системные

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/health` | Проверка здоровья API и БД |

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

### Регистрация на событие

```bash
curl -X POST http://localhost:8001/api/v1/events/{event_id}/register \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## Тестирование

Запуск тестов (pytest):

```bash
pytest --cov=app
```

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
