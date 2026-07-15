#  Сервис авторизации по номеру телефона

REST API сервис для регистрации и аутентификации пользователей по номеру телефона с системой инвайт-кодов.

##  Возможности

-  **Авторизация по номеру телефона** - вход без пароля, только код из SMS
-  **4-значный код верификации** - отправка кода с задержкой 1-2 секунды
-  **Инвайт-коды** - 6-значный код для приглашения друзей
-  **Социальный функционал** - просмотр приглашенных пользователей
-  **JWT авторизация** - безопасные токены доступа
-  **REST API** - полный набор эндпоинтов
-  **Bootstrap интерфейс** - красивые страницы для тестирования
-  **Swagger/ReDoc** - автоматическая документация API

## 🛠 Технологии

| Компонент | Технология |
|-----------|------------|
| Язык | Python 3.12 |
| Фреймворк | Django 5.0.6 |
| API | Django REST Framework 3.15.1 |
| Аутентификация | JWT (SimpleJWT) |
| База данных | PostgreSQL 15 |
| Кэш/Коды | Redis 7 |
| Документация | drf-yasg (Swagger/ReDoc) |
| Контейнеризация | Docker, Docker Compose |
| Фронтенд | Bootstrap 5 |

##  Структура проекта
Diploma/
├── config/ # Настройки Django
│ ├── settings.py # Основные настройки
│ ├── urls.py # URL маршруты
│ └── wsgi.py # WSGI приложение
├── users/ # Приложение пользователей
│ ├── models.py # Модель CustomUser
│ ├── managers.py # Кастомный менеджер
│ └── admin.py # Админ-панель
├── auth_app/ # Приложение авторизации
│ ├── views.py # Web и API вьюхи
│ ├── services.py # Бизнес-логика
│ ├── redis_client.py # Клиент Redis
│ ├── serializers.py # DRF сериализаторы
│ ├── urls.py # Web маршруты
│ └── urls_api.py # API маршруты
├── templates/ # HTML шаблоны
│ ├── base.html
│ ├── auth/
│ │ ├── login.html
│ │ └── verify.html
│ └── users/
│ └── profile.html
├── static/ # Статические файлы
│ └── css/
│ └── style.css
├── Dockerfile # Docker образ
├── docker-compose.yml # Docker Compose
├── requirements.txt # Зависимости
├── entrypoint.sh # Точка входа
└── README.md # Документация

# Запуск

### Через Docker (рекомендуется)


##  1. Клонируйте репозиторий
git clone <repository-url>
cd Diploma

## 2. Создайте .env файл
cp .env.example .env

## 3. Запустите контейнеры
docker-compose up --build

## 4. Откройте в браузере
 http://localhost:8000/

# Локальный запуск (без Docker)

## 1. Создайте виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
## .venv\Scripts\activate   # Windows

## 2. Установите зависимости
pip install -r requirements.txt

## 3. Создайте .env
cp .env.example .env

## 4. Примените миграции
python manage.py makemigrations
python manage.py migrate

## 5. Создайте суперпользователя
python manage.py createsuperuser

## 6. Запустите сервер
python manage.py runserver




# API Эндпоинты

## Web интерфейс

Метод	URL	Описание
GET	/	Страница входа
POST	/	Отправка кода
GET	/verify/	Страница подтверждения
POST	/verify/	Подтверждение кода
GET	/profile/	Профиль пользователя
POST	/profile/	Активация инвайт-кода
GET	/logout/	Выход

## REST API

Метод	URL	Описание
POST	/api/send-code/	Отправка кода
POST	/api/verify/	Подтверждение кода + получение токенов
GET	/api/profile/	Профиль пользователя
POST	/api/activate-invite/	Активация инвайт-кода
POST	/api/refresh/	Обновление access токена
POST	/api/logout/	Выход (blacklist токена)

# Документация API

Swagger UI: http://localhost:8000/swagger/
ReDoc: http://localhost:8000/redoc/

# Безопасность

✅ 3 попытки ввода кода → блокировка на 5 минут

✅ TTL кода 5 минут

✅ JWT с ограниченным сроком жизни

✅ Blacklist для refresh токенов

✅ Нормализация номеров телефонов

✅ Уникальность инвайт-кодов

# Тестирование

## Запуск тестов
python manage.py test

## В Docker
docker-compose exec web python manage.py test

#Docker команды

## Сборка и запуск
docker-compose up --build

## Запуск в фоновом режиме
docker-compose up -d

## Остановка
docker-compose down

## Просмотр логов
docker-compose logs -f web

## Запуск команд внутри контейнера
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py test

# Контакты
 Wizard
