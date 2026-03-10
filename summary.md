# EventHub API — Project Summary

**Дата начала:** 2026-03-10  
**Стек:** FastAPI + MongoDB + Redis + Docker  
**Задача:** Пет-проект — платформа для организации ивентов

---

## 📋 Требования (кратко)

### Сущности
- **User** — пользователи (роли: user, admin), JWT аутентификация
- **Event** — события (CRUD, пагинация, фильтры)
- **Registration** — регистрация на ивенты (лимит участников)

### Технические требования
- ASGI: FastAPI
- БД: MongoDB (Motor — асинхронный драйвер)
- Кеш/Очереди: Redis (кеш событий 5 мин, профилей 10 мин + очереди задач)
- JWT: access 15 мин, refresh 7 дней
- Docker: API, MongoDB, Redis
- CI/CD: GitHub Actions (lint, test, build)
- Тесты: pytest + httpx

### API Endpoints
```
POST /api/auth/register       — Регистрация
POST /api/auth/login          — Логин
POST /api/auth/refresh        — Обновление токена
GET  /api/users/me            — Мой профиль
PUT  /api/users/me            — Обновление профиля
GET  /api/events              — Список событий
POST /api/events              — Создание события
GET  /api/events/{id}         — Одно событие
PUT  /api/events/{id}         — Обновление события
DELETE /api/events/{id}       — Удаление события
POST /api/events/{id}/register     — Регистрация на ивент
DELETE /api/events/{id}/register   — Отмена регистрации
GET  /api/events/{id}/participants — Участники ивента
GET  /api/registrations/me    — Мои регистрации
```

### Дополнительные фичи
- Rate limiting на `/api/auth/login` (10 запросов/мин)
- Graceful shutdown
- Health check `/health`
- JSON логирование

---

## 📁 Структура проекта

```
eventhub-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # Точка входа, создание приложения
│   ├── config.py            # Настройки (env variables)
│   ├── database.py          # Подключение к MongoDB
│   ├── redis_client.py      # Подключение к Redis (кеш + очереди)
│   │
│   ├── models/              # MongoDB модели
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── event.py
│   │   └── registration.py
│   │
│   ├── schemas/             # Pydantic схемы (request/response)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── event.py
│   │   ├── registration.py
│   │   └── token.py
│   │
│   ├── api/                 # API роуты
│   │   ├── __init__.py
│   │   ├── deps.py          # Зависимости (get_current_user, etc.)
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── events.py
│   │   └── registrations.py
│   │
│   ├── services/            # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── auth.py          # JWT, password hash
│   │   ├── user.py
│   │   ├── event.py
│   │   └── registration.py
│   │
│   ├── tasks/               # Асинхронные задачи (Redis queues)
│   │   ├── __init__.py
│   │   ├── worker.py        # ARQ worker
│   │   └── tasks.py         # Задачи (email, валидация)
│   │
│   ├── middleware/          # Middleware
│   │   ├── __init__.py
│   │   ├── rate_limiter.py
│   │   └── logging.py
│   │
│   └── utils/               # Утилиты
│       ├── __init__.py
│       └── health.py        # Health checks
│
├── tests/                   # Тесты
│   ├── __init__.py
│   ├── conftest.py          # Fixtures (pytest)
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_events.py
│   └── test_registrations.py
│
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions
│
├── docker-compose.yml       # MongoDB, Redis, API
├── Dockerfile               # API контейнер
├── requirements.txt         # Python зависимости
├── .env.example             # Пример переменных окружения
├── .gitignore
└── summary.md               # Этот файл
```

---

## 🚧 Прогресс

| Этап | Задача | Статус |
|------|--------|--------|
| 1 | Структура проекта | ✅ |
| 1 | Docker Compose (MongoDB, Redis, API) | ⬜ |
| 1 | FastAPI + Motor (MongoDB) | ⬜ |
| 2 | Pydantic схемы | ⬜ |
| 2 | JWT аутентификация | ⬜ |
| 2 | CRUD пользователей | ⬜ |
| 2 | CRUD событий | ⬜ |
| 2 | Регистрация на ивенты | ⬜ |
| 3 | Redis кэширование | ⬜ |
| 3 | Redis очереди (ARQ) | ⬜ |
| 3 | Rate limiting | ⬜ |
| 3 | Health check | ⬜ |
| 3 | Graceful shutdown | ⬜ |
| 3 | JSON логирование | ⬜ |
| 4 | Тесты (pytest + httpx) | ⬜ |
| 4 | GitHub Actions CI/CD | ⬜ |

---

## 📝 Заметки

### Решения
- **Очереди задач:** ARQ (легковесный, асинхронный, совместим с FastAPI)
- **JWT библиотека:** PyJWT или python-jose
- **Password hash:** passlib + bcrypt

### Переменные окружения (планируемые)
```
MONGODB_URL=mongodb://mongodb:27017
REDIS_URL=redis://redis:6379
SECRET_KEY=...
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## 🔜 Следующие шаги

1. ✅ Создать структуру директорий
2. ⬜ Написать docker-compose.yml
3. ⬜ Настроить FastAPI приложение
4. ⬜ Реализовать JWT аутентификацию

---

## 📝 История изменений

### 2026-03-10 — Начало

**Что сделано:**
- Создана структура директорий проекта
- Создан `summary.md` для отслеживания прогресса
- Создан `docker-compose.yml` (API, MongoDB, Redis)
- Создан `Dockerfile`
- Создан `requirements.txt`
- Создан `.env.example`
- Создан `.gitignore`
- Создан `app/config.py`

**Важное:**
- Код пишет пользователь (я только отвечаю на вопросы)
- Стек: FastAPI + MongoDB (Motor) + Redis (ARQ) + Docker
- Очереди: ARQ (асинхронный)
- JWT: access 15 мин, refresh 7 дней

---

### 2026-03-10 — Работа над database.py

**Проблема:** Пользователь очистил `requirements.txt`, `config.py`, `.env.example` — не понимает что и зачем.

**Объяснено:**
- Motor — асинхронный драйвер для MongoDB (нужен для FastAPI)
- Архитектура приложения (слои): API → Services → Models → Database
- Структура файлов: schemas (валидация), api (endpoints), services (логика), models (CRUD)

**Следующий шаг:** `app/database.py` — подключение к MongoDB через Motor

**Зависимость:** `pip install motor`

---

### 2026-03-10 — Настройка конфигурации (pydantic-settings)

**Решение:**
- `pydantic-settings` для управления настройками через env переменные
- Вложенная структура: `Settings.mongo_db: MongoDBClient`
- `env_nested_delimiter='.'` — разделитель для вложенности

**Формат `.env`:**
```
MONGO_DB.URL=mongodb://localhost:27017
MONGO_DB.DB_NAME=eventhub
```

**Файлы:**
- `app/config.py` — основной класс настроек
- `app/config_models/data_base_config.py` — модель MongoDB настроек

**Следующий шаг:** Завершить `app/database.py` — подключение к MongoDB

---

### 2026-03-10 — Правило работы

**ВАЖНО:** 
- Я (AI) — учитель/ментор, НЕ пишу код за пользователя
- Объясняю концепции, инструменты, лучшие практики
- Даю псевдокод, направления, ссылки на документацию
- Пользователь пишет код САМ — так он учится
- Если пользователь застрял — даю подсказку, но не готовое решение

**Цель:** Пользователь должен НАУЧИТЬСЯ, а не получить готовое.

---
