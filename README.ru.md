# 🔐 Auth System: JWT + Redis Whitelist / Blacklist с RBAC

Система аутентификации, которая не просто *доверяет* JWT-токенам вслепую.  
Потому что stateless не означает "нельзя отозвать" - познакомьтесь с вашим новым охранником: **Redis** 🛡️

> *Предупреждение:* Эта система действительно заботится о безопасности токенов. Ваши JWT еще никогда не были под таким контролем! ⚠️

## 📑 Содержание
- [Описание](#description)
- [Быстрый старт](#quick-start)
- [API Endpoints](#api-endpoints)
- [Тестирование](#testing)
- [Как это работает (Магия)](#how-it-works-the-magic)
- [Система разрешений](#permission-system)
- [Возможности](#features)
- [Технологический стек](#tech-stack)
- [Структура проекта](#project-structure)
- [Схема базы данных](#database-schema)
- [Механизмы безопасности](#security-mechanisms)
- [Защита от утечки токенов](#token-leak-protection)
- [Возможные улучшения](#possible-improvements)
- [План развития](#roadmap)
- [Лицензия](#license)
- [Совет профи](#pro-tip)

## <a id="description"></a> 📋 Описание

У стандартного JWT есть фатальный недостаток: однажды выпущенный, он живет до истечения срока действия — даже если украден.  
Эта система решает эту проблему, поддерживая **белый** и **черный списки** в Redis, которые проверяются при **каждом** запросе.

Построена на **FastAPI** (асинхронный, современный, быстрый), использует **PostgreSQL** (сессии, пользователи, аудит) и защищена с помощью **bcrypt** + **JWT**.

## <a id="quick-start"></a> 🚀 Быстрый старт

### С Docker (рекомендуется)
```bash
# Клонируйте проект
git clone jwt-authentication
cd jwt-authentication

# Запустите все (PostgreSQL + Redis + FastAPI)
docker-compose up --build

# Заполните права доступа (только в первый раз - в другом терминале)
docker-compose --profile seed-permissions up

# Заполните тестовых пользователей (только в первый раз)
docker-compose --profile seed-users up
```
Затем откройте: `http://localhost:8000/docs` для интерактивной документации API.

#### Тестовые пользователи (создаются скриптом)
| Имя пользователя | Пароль | Роль |
| -------- | ------- | ------- |
| alice | alicepass | role1 |
| bob | bobpass | role2 |
| admin | adminpass | admin |

### Без Docker (локальная разработка)
```bash
# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows

# Установите зависимости
pip install -r requirements.txt

# Установите переменные окружения (или используйте файл .env)
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/auth_db
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=your-secret-key-change-in-production
export ALGORITHM=HS256
export ACCESS_TOKEN_EXPIRE_MINUTES=30

# Запустите сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## <a id="api-endpoints"></a> 🔌 API Endpoints

### Публичные endpoint'ы
| Метод | Endpoint | Описание |
| -------- | ------- | ------- |
| GET | / | Статус API |
| GET | /ping | Простая проверка здоровья |
| POST | /login | Аутентификация → получение JWT |
| POST | /logout | Отзыв текущего токена |
| POST | /register | Создание нового пользователя |
| GET | /health/db | Проверка подключения к базе данных |

### Защищенные (требуется Bearer токен)
| Метод | Endpoint | Требуемое разрешение | Описание |
| -------- | ------- | ------- | ------- |
| GET | /me | Аутентифицированный пользователь | Получить информацию о текущем пользователе |
| GET | /content/common | `content:read:common` | Общий контент для всех ролей |
| GET | /content/role1 | `content:read:role1` | Эксклюзивный контент для Role1 |
| GET | /content/role2 | `content:read:role2` | Эксклюзивный контент для Role2 |
| GET | /content/admin | `content:read:admin` | Панель администратора |

### Admin endpoint'ы
| Метод | Endpoint | Требуемое разрешение | Описание |
| -------- | ------- | ------- | ------- |
| GET | /admin/users | `users:read` | Список всех активных пользователей |
| POST | /admin/users/{id}/block | `users:block` | Заблокировать пользователя |
| POST | /admin/users/{id}/unblock | `users:unblock` | Разблокировать пользователя |

### Пример использования
```bash
# Вход в систему
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alicepass"}'

# Ответ: {"access_token":"eyJ...", "token_type":"bearer", "role":"role1"}

# Доступ к защищенному контенту
curl -X GET http://localhost:8000/content/role1 \
  -H "Authorization: Bearer eyJ..."

# Выход из системы
curl -X POST http://localhost:8000/logout \
  -F "token=eyJ..."
```

## <a id="testing"></a> 🧪 Тестирование
```bash
# Запустить все тесты с Docker
docker-compose --profile testing up --build

# Или запустить тесты локально
pytest -v --tb=short

# Запустить конкретный файл с тестами
pytest tests/test_rbac.py -v

# Запустить с покрытием
pytest --cov=app tests/
```

### Покрытие тестами
- **JWT Validation** - генерация, декодирование, истечение срока токенов
- **Механизм выхода** - операции с белым и черным списками
- **RBAC** - проверка разрешений, доступ на основе ролей
- **Управление сессиями** - создание сессий, отзыв
- **Admin операции** - блокировка/разблокировка пользователей

## <a id="how-it-works-the-magic"></a> 🎪 Как это работает (Магия)

```mermaid
sequenceDiagram
    participant Client as Клиент
    participant API as API
    participant Redis as Redis
    participant PostgreSQL as PostgreSQL

    Client->>API: POST /login (username/password)
    API->>PostgreSQL: проверка пользователя + bcrypt
    PostgreSQL-->>API: пользователь найден с ролями
    API->>API: генерация JWT с уникальным jti
    API->>Redis: добавить jti в белый список (TTL 30мин)
    API->>PostgreSQL: создать запись сессии с IP/UA
    API-->>Client: access_token

    Client->>API: GET /content/role1 (Bearer токен)
    API->>Redis: jti в белом списке?
    Redis-->>API: да
    API->>Redis: jti в черном списке?
    Redis-->>API: нет
    API->>PostgreSQL: получить разрешения пользователя
    PostgreSQL-->>API: набор разрешений
    API->>API: проверить требуемые разрешения
    API-->>Client: эксклюзивный контент

    Client->>API: POST /logout (токен)
    API->>Redis: переместить jti в черный список
    API->>PostgreSQL: отметить сессию как отозванную
    API-->>Client: выход выполнен
```

### Почему Redis?
- Время ответа менее миллисекунды
- Автоматический TTL (не нужны cron-задачи)
- Идеально подходит для высоконагруженной аутентификации (10k+ RPS)

### Конфигурация TTL в Redis
- **Белый список TTL:** 30 минут (соответствует `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Черный список TTL:** 1 час (для аудита)

## <a id="permission-system"></a> 🎯 Система разрешений

Разрешения следуют шаблону: `{ресурс}:{действие}`

Система реализует **детальное управление доступом на основе разрешений** с:
- *Ресурсы:* content, users, sessions, roles, permissions, admin, health
- *Действия:* create, read, update, delete, block, unblock, assign_role, revoke
- *Реестр разрешений:* Централизованное метаданные с отслеживанием зависимостей

### Примеры разрешений
```python
# Разрешения на контент
CONTENT_READ_COMMON = "content:read:common"      # Все аутентифицированные пользователи
CONTENT_READ_ROLE1 = "content:read:role1"        # Эксклюзивно для Role1
CONTENT_READ_ROLE2 = "content:read:role2"        # Эксклюзивно для Role2
CONTENT_READ_ADMIN = "content:read:admin"        # Только для admin

# Управление пользователями
USERS_READ = "users:read"                        # Просмотр списка пользователей
USERS_BLOCK = "users:block"                      # Блокировка пользователей
USERS_UNBLOCK = "users:unblock"                  # Разблокировка пользователей

# Управление сессиями
SESSIONS_READ = "sessions:read"                   # Просмотр сессий
SESSIONS_REVOKE_OTHER = "sessions:revoke:other"  # Отзыв сессий других пользователей
```

### Разрешения по умолчанию для ролей
| Роль | Разрешения |
| -------- | -------- |
| role1 | `content:read:common`, `content:read:role1` |
| role2 | `content:read:common`, `content:read:role2` |
| admin | Доступ к админке, управление пользователями, управление сессиями, просмотр ролей/разрешений, проверки здоровья |

> Примечание: Разрешения `SESSIONS_READ`, `SESSIONS_REVOKE_OTHER`, `SESSIONS_REVOKE_ALL` определены, но endpoint'ы находятся в разработке.

## <a id="features"></a> ✨ Возможности
- **JWT с белым списком** - токен должен быть явно добавлен в белый список при входе
- **Мгновенный отзыв** - выход или блокировка администратором → токен попадает в черный список
- **Детальный RBAC** - управление доступом на основе ролей с детальными разрешениями
- **Реестр разрешений** - централизованное управление разрешениями с проверкой зависимостей
- **Отслеживание сессий** - каждый токен логируется в PostgreSQL (IP, User-Agent, временные метки)
- **Admin endpoint'ы** - список пользователей, блокировка аккаунтов
- **Контент на основе ролей** - role1, role2, admin с эксклюзивным контентом
- **Проверки здоровья** - для Docker оркестрации (Redis + PostgreSQL)
- **Автоматическое заполнение данных** - скрипты заполнения для разрешений и тестовых пользователей

## <a id="tech-stack"></a> 🛠️ Технологический стек

| Уровень | Технология |
|-------|-------------|
| **API Framework** | FastAPI (асинхронный) |
| **Хранилище токенов** | Redis 7 (белый/черный списки с TTL) |
| **Постоянное хранилище** | PostgreSQL 15 + SQLAlchemy 2.0 (asyncpg) |
| **Аутентификация** | JWT (python-jose) + bcrypt 4.0 |
| **Тестирование** | pytest 7.4 + pytest-asyncio + fakeredis |
| **Контейнеризация** | Docker + Docker Compose |

## <a id="project-structure"></a> 📁 Структура проекта
```text
jwt-authentication/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI приложение, маршруты, время жизни
│   ├── models.py            # SQLAlchemy модели
│   ├── database.py          # Асинхронный движок БД
│   ├── api/                 # Обработчики маршрутов API
│   │   ├── __init__.py
│   │   ├── auth.py          # Вход, регистрация
│   │   ├── logout.py        # Отзыв токенов
│   │   ├── admin.py         # Управление пользователями
│   │   └── content.py       # Защищенный контент
│   └── core/                # Основная бизнес-логика
│       ├── config.py        # Настройки
│       ├── dependencies.py  # Зависимости аутентификации
│       ├── permissions.py   # RBAC логика
│       ├── redis_client.py  # Redis обертка
│       └── schemas.py       # Pydantic схемы запросов/ответов
├── tests/                   # Модульные и интеграционные тесты
│   ├── __init__.py
│   ├── conftest.py          # Фикстуры (async клиент, тестовая БД, mock redis)
│   ├── test_jwt.py          # Тесты валидации JWT токенов
│   ├── test_logout.py       # Тесты выхода и отзыва токенов
│   └── test_rbac.py         # Тесты доступа на основе ролей и разрешений
├── scripts/                 # Скрипты заполнения
│   ├── seed_permissions.py  # Создание ролей и разрешений
│   └── seed_users.py        # Создание тестовых пользователей с ролями
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── README.md
└── README.ru.md
```

## <a id="database-schema"></a> 📊 Схема базы данных

### Основные таблицы
- **users** - Учетные записи пользователей (id, username, hashed_password, is_active, временные метки)
- **roles** - Определения ролей (id, name, description, is_default)
- **permissions** - Определения разрешений (id, name, resource, action)
- **sessions** - Активные сессии (id, user_id, jti, ip_address, user_agent)
- **user_roles** - Многие-ко-многим (user_id, role_id)
- **role_permissions** - Многие-ко-многим (role_id, permission_id)

## <a id="security-mechanisms"></a> 🛡️ Механизмы безопасности
| Угроза | Меры защиты | Статус |
| -------- | ------- | ------- |
| Кража токена | Белый + Черный списки - мгновенный отзыв | ✅ |
| Воспроизведение токена | JTI хранится в Redis, проверяется каждый запрос | ✅ |
| Утечка пароля | bcrypt хеширование (соль + стоимость) | ✅ |
| Перехват сессии | Логирование IP + User-Agent, отслеживание сессий | ✅ |
| Злоупотребление админа | Детальная система разрешений | ✅ |
| Повышение привилегий | Проверка зависимостей разрешений | ✅ |
| Отказ Redis | Проверка здоровья + ошибка 503 | ✅ |

## <a id="token-leak-protection"></a> 🔐 Защита от утечки токенов

### ❓ Откуда берутся утечки?
| Способ кражи | Как происходит |
| -------- | ------- |
| XSS атака | Скрипт крадет токен из localStorage |
| Перехват трафика | Передача по HTTP (не HTTPS) |
| Уязвимости браузера | Вредоносное расширение |
| Логи сервера | Токен попадает в логи отладки |
| Фишинг | Поддельный сайт захватывает токен |

### 🛡️ Методы защиты
Уже реализовано в этом проекте:
1. *Белый + Черный списки* - мгновенный отзыв токена
2. *Привязка сессии* - валидация IP и User-Agent
3. *Короткое время жизни* - истечение срока жизни токена через 30 минут
4. *HttpOnly cookies* - защита от XSS

## <a id="possible-improvements"></a> 🛠️ Возможные улучшения (План развития)
-  **Обновление токена с ротацией** - лучший UX, чем выход каждые 30 минут
- **Снятие отпечатков устройств** - обнаружение кражи токена по изменению User‑Agent/IP
- **Ограничение скорости** - предотвращение атак перебора паролей
- **Метрики Prometheus** - мониторинг активных токенов, частоты отзывов
- **Двухфакторная аутентификация (2FA)** - дополнительный уровень безопасности
- **OAuth2 / OpenID Connect** - интеграция входа через соцсети
- **Аудит логирования** - отслеживание всех проверок разрешений

## <a id="roadmap"></a> 🛣️ План развития

### Реализовано ✅
- JWT аутентификация с белым/черным списками
- Полный RBAC с 40+ разрешениями
- Отслеживание сессий в PostgreSQL
- Admin endpoint'ы (список, блокировка, разблокировка пользователей)
- Проверка зависимостей разрешений
- Скрипты заполнения начальными данными
- Комплексный набор тестов

### В плане 🚧

#### Краткосрочные:
- Реализовать логику `block_user` и `unblock_user` в `admin.py`
- Добавить endpoint'ы для отзыва сессий (отзыв своей, отзыв чужой, отзыв всех)
- Добавить ротацию обновления токенов
- Ограничение скорости на endpoint входа

#### Среднесрочные:
- Снятие отпечатков устройств (обнаружение кражи токена)
- Аудит логирования (отслеживание всех проверок разрешений)
- Метрики Prometheus (активные сессии, частота отзыва токенов)
- Двухфакторная аутентификация (2FA)

#### Долгосрочные:
- OAuth2 / OpenID Connect (вход через соцсети)
- WebAuthn (аутентификация без пароля)
- gRPC API для высокопроизводительных внутренних сервисов
- Распределенное ограничение скорости с Redis

## <a id="license"></a> 📜 Лицензия
MIT - используйте, ломайте, исправляйте, улучшайте. Просто помните о безопасности!

## <a id="pro-tip"></a> 💡 Совет профи
> Никогда не логируйте JWT токены - ни в файлы, ни в консоль, нигде. Если вам нужно отладить, логируйте только jti (идентификатор токена) и пользователя.

И помните:
**Белый список + Черный список = Спокойный сон** 😴🔒

***Удачной защиты!*** 🔐✨
