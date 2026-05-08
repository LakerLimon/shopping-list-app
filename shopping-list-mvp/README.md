# MVP: Список покупок с общим доступом

Это рабочий MVP проекта: backend на Django REST Framework + PostgreSQL + JWT + мобильный web-прототип для проверки сценария без Android Studio.

Главный сценарий уже реализован:

1. пользователь регистрируется;
2. создаёт список покупок;
3. создаёт приглашение;
4. второй пользователь принимает приглашение;
5. участники добавляют товары;
6. товар отмечается как купленный;
7. купленный товар попадает в историю;
8. остальные участники получают внутренние уведомления.

## Что входит

- Django REST Framework API.
- PostgreSQL через Docker Compose.
- JWT-авторизация.
- Регистрация и вход по email + паролю.
- Списки покупок.
- Роли: `OWNER`, `MEMBER`.
- Приглашения по UUID-коду.
- Товары: название, количество, единица измерения, цена, категория, комментарий.
- Редактирование, удаление, отметка товара как купленного.
- История купленных товаров.
- Внутренние уведомления в БД.
- Мобильный web-прототип по адресу `/`.
- Админка Django.
- Тест основного пользовательского сценария.

## Быстрый запуск через Docker

Из корня проекта:

```bash
docker compose up --build
```

После запуска открой:

```text
http://localhost:8000/
```

API доступно по адресу:

```text
http://localhost:8000/api/
```

## Проверка тестами

В отдельном терминале:

```bash
docker compose exec api python manage.py test
```

## Создание администратора

```bash
docker compose exec api python manage.py createsuperuser
```

Админка:

```text
http://localhost:8000/admin/
```

## Запуск без Docker

Нужен локальный PostgreSQL. По умолчанию `.env.example` ждёт БД на `localhost:5433`, как в Docker Compose.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows PowerShell
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

## Основные API endpoints

### Авторизация

| Метод | Endpoint | Назначение |
|---|---|---|
| `POST` | `/api/auth/register/` | регистрация |
| `POST` | `/api/auth/login/` | вход |
| `POST` | `/api/auth/refresh/` | обновление access token |
| `GET` | `/api/auth/me/` | текущий пользователь |

### Списки

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/api/lists/` | мои списки |
| `POST` | `/api/lists/` | создать список |
| `GET` | `/api/lists/{id}/` | получить список |
| `PATCH` | `/api/lists/{id}/` | переименовать список |
| `DELETE` | `/api/lists/{id}/` | удалить список, только владелец |
| `POST` | `/api/lists/{id}/invite/` | создать приглашение, только владелец |
| `GET` | `/api/lists/{id}/members/` | участники списка |

### Приглашения

| Метод | Endpoint | Назначение |
|---|---|---|
| `POST` | `/api/invitations/{code}/accept/` | принять приглашение |

### Товары

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/api/lists/{id}/products/` | активные товары списка |
| `POST` | `/api/lists/{id}/products/` | добавить товар |
| `PATCH` | `/api/products/{id}/` | изменить товар |
| `DELETE` | `/api/products/{id}/` | удалить товар |
| `POST` | `/api/products/{id}/buy/` | отметить купленным |
| `GET` | `/api/lists/{id}/history/` | история покупок |

### Уведомления

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/api/notifications/` | мои уведомления |
| `PATCH` | `/api/notifications/` | отметить уведомления прочитанными |

## Примеры curl

### 1. Регистрация владельца

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@example.com","password":"strong-pass-123"}'
```

Сохрани `access` из ответа.

### 2. Создание списка

```bash
curl -X POST http://localhost:8000/api/lists/ \
  -H "Authorization: Bearer OWNER_ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"name":"Продукты на неделю"}'
```

### 3. Создание приглашения

```bash
curl -X POST http://localhost:8000/api/lists/1/invite/ \
  -H "Authorization: Bearer OWNER_ACCESS"
```

### 4. Добавление товара

```bash
curl -X POST http://localhost:8000/api/lists/1/products/ \
  -H "Authorization: Bearer OWNER_ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"name":"Молоко","quantity":"2","unit":"л","estimated_price":"120.00","category_name":"Молочка","comment":"2.5%"}'
```

### 5. Принятие приглашения вторым пользователем

```bash
curl -X POST http://localhost:8000/api/invitations/INVITE_CODE/accept/ \
  -H "Authorization: Bearer MEMBER_ACCESS"
```

### 6. Отметка товара как купленного

```bash
curl -X POST http://localhost:8000/api/products/1/buy/ \
  -H "Authorization: Bearer MEMBER_ACCESS"
```
