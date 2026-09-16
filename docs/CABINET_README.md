# 🔐 ЛИЧНЫЙ КАБИНЕТ КЛИЕНТОВ - ПОЛНОЕ РУКОВОДСТВО

**Статус:** Полная система разработана
**Запуск:** 1 октября 2026
**Стек:** React + Flask + PostgreSQL

---

# 📋 СОДЕРЖАНИЕ

1. [Обзор системы](#обзор-системы)
2. [Функционал](#функционал)
3. [Архитектура](#архитектура)
4. [Разработка](#разработка)
5. [Интеграция](#интеграция)
6. [Деплой](#деплой)

---

# 🎯 ОБЗОР СИСТЕМЫ

## Что это

Личный веб-кабинет для клиентов, где они могут:
- Просматривать все полученные письма
- Управлять подпиской (видеть дату продления)
- Скачивать письма в PDF
- Видеть историю платежей
- Получать уведомления о новых письмах

## Для кого

- **Клиенты**: видят свои письма и подписку
- **Алиса**: видит аналитику, управляет клиентами
- **Бот**: синхронизирует данные

## Когда запускается

**1 октября 2026** - после месяца работы бота
(дает время на тестирование и сбор обратной связи)

---

# ✨ ФУНКЦИОНАЛ

## КЛИЕНТСКИЙ ИНТЕРФЕЙС

### 1. Вход (через Telegram)
```
- Одна кнопка "Login with Telegram"
- Автоматическая регистрация
- Быстрый доступ без паролей
```

### 2. Dashboard (главная страница)
```
- Статус подписки (тип, цена, дата продления)
- Количество полученных писем
- 3 последних письма
- История платежей (короткая)
```

### 3. Мои письма
```
- Список всех писем (с фильтром по типу)
- Поиск по содержанию вопроса
- Просмотр полного текста
- Скачивание в PDF
- Добавление в избранное
- Поделиться (копировать ссылку)
```

### 4. Управление подпиской
```
- Текущий тип подписки
- Сумма/месяц
- Дата продления
- Количество писем в месяц vs использовано
- Кнопки: Паузировать, Обновить, Отменить
```

### 5. История платежей
```
- Все платежи (дата, сумма, статус)
- Фильтр по месяцам
- Экспорт в CSV (позже)
```

### 6. Профиль
```
- Имя, юзернейм
- Email (для уведомлений)
- Дата присоединения
- Статистика (писем прочитано, любимых и т.д.)
```

---

# 🏗️ АРХИТЕКТУРА

## ТЕХНОЛОГИЧЕСКИЙ СТЕК

### Backend
```
Python 3.8+
Flask 3.0
SQLAlchemy 2.0
Flask-JWT-Extended
Flask-CORS
PostgreSQL
Gunicorn
```

### Frontend
```
React 18
Tailwind CSS 3
Axios
React Router 6
React Query
```

### Deployment
```
Backend: Railway/Heroku
Frontend: Vercel/Netlify
Database: PostgreSQL
```

## ДИАГРАММА ПОТОКА

```
Frontend (React)
    ↓
API (Flask)
    ↓
Database (PostgreSQL)
    ↓
TG Bot (sync)
    ↓
Google Sheets (sync)
```

## ТАБЛИЦЫ БД

```
users
├─ id (PK)
├─ telegram_id (UNIQUE)
├─ username
├─ first_name
├─ email
├─ created_at
├─ last_login
└─ is_customer

subscriptions
├─ id (PK)
├─ user_id (FK)
├─ type (письма/премиум/вип)
├─ price
├─ start_date
├─ renewal_date
├─ status (active/paused/cancelled)
└─ created_at

letters
├─ id (PK)
├─ user_id (FK)
├─ question
├─ type (письмо/дневник/сценарий)
├─ content
├─ created_at
├─ read_at
├─ is_favorite
└─ share_token (для публичного доступа)

payments
├─ id (PK)
├─ user_id (FK)
├─ amount
├─ type (subscription/single)
├─ status
├─ created_at
└─ reference_id
```

---

# 💻 РАЗРАБОТКА

## СТРУКТУРА ПРОЕКТА

```
alisa-cabinet/
├── backend/
│   ├── app.py (Flask приложение)
│   ├── models.py (SQLAlchemy модели)
│   ├── routes.py (API endpoints)
│   ├── auth.py (Аутентификация)
│   ├── requirements.txt
│   ├── .env.example
│   └── config.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── LetterList.jsx
│   │   │   ├── LetterDetail.jsx
│   │   │   ├── Subscription.jsx
│   │   │   ├── Profile.jsx
│   │   │   └── Login.jsx
│   │   ├── api/
│   │   │   └── client.js
│   │   ├── styles/
│   │   │   ├── index.css
│   │   │   └── components.css
│   │   ├── App.jsx
│   │   └── index.js
│   ├── public/
│   │   └── index.html
│   ├── package.json
│   └── .env.example
└── README.md
```

## УСТАНОВКА (локально)

### Backend

```bash
cd backend

# Виртуальное окружение
python -m venv venv
source venv/bin/activate  # Mac/Linux
# или
venv\Scripts\activate  # Windows

# Зависимости
pip install -r requirements.txt

# БД
export DATABASE_URL="sqlite:///alisa.db"
python -c "from app import db; db.create_all()"

# Запуск
python app.py
# Откроется на http://localhost:5000
```

### Frontend

```bash
cd frontend

# Node.js зависимости
npm install

# Запуск development сервера
npm start
# Откроется на http://localhost:3000
```

## API ENDPOINTS

### Аутентификация
```
POST /api/auth/telegram
  Вход через Telegram
  
GET /api/auth/verify
  Проверить токен (JWT)
```

### Профиль
```
GET /api/user/profile
  Получить профиль
  
PUT /api/user/profile
  Обновить профиль
```

### Письма
```
GET /api/letters
  Список писем (с пагинацией и фильтром)
  
GET /api/letters/<id>
  Полное письмо
  
GET /api/letters/<id>/download
  Скачать PDF
  
PUT /api/letters/<id>/favorite
  Добавить/удалить из избранного
```

### Подписка
```
GET /api/subscription
  Текущая подписка
  
GET /api/subscription/stats
  Статистика (писем использовано и т.д.)
  
POST /api/subscription/pause
  Приостановить
  
POST /api/subscription/resume
  Возобновить
  
POST /api/subscription/cancel
  Отменить
```

### Платежи
```
GET /api/payments
  История платежей
```

---

# 🔗 ИНТЕГРАЦИЯ

## С TG БОТОМ

### Отправка ссылки на кабинет

Когда клиент активирует подписку:

```python
# В bot_full_code.py добавляем:

cabinet_url = "https://alisa-letters.com/cabinet"

bot.send_message(chat_id, f"""
✅ ПОДПИСКА АКТИВИРОВАНА!

Смотреть все письма в кабинете:
{cabinet_url}

Там же ты сможешь:
- Скачивать письма в PDF
- Видеть дату продления
- Управлять подпиской
- Смотреть историю платежей
""")
```

### Синхронизация данных

Каждый час бот синхронизирует данные:

```python
@scheduler.scheduled_job('cron', minute=0)
def sync_data():
    """Синхронизирует Google Sheets с БД кабинета"""
    
    # Получаем новые заказы
    new_orders = get_new_orders_from_sheets()
    
    for order in new_orders:
        # Создаём письмо в БД кабинета
        letter = Letter(
            user_id=order['user_id'],
            question=order['question'],
            letter_type=order['type'],
            content=generate_letter(order['question'], order['type'])
        )
        db.session.add(letter)
    
    # Получаем новые подписки
    new_subs = get_new_subscriptions_from_sheets()
    
    for sub in new_subs:
        # Создаём подписку в БД кабинета
        subscription = Subscription(
            user_id=sub['user_id'],
            subscription_type=sub['type'],
            price=sub['price'],
            renewal_date=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(subscription)
    
    db.session.commit()
```

---

# 🚀 ДЕПЛОЙ

## BACKEND (на Railway)

```bash
# 1. Создать Procfile
echo "web: gunicorn app:app" > Procfile

# 2. Создать requirements.txt
pip freeze > requirements.txt

# 3. Railway CLI
npm install -g @railway/cli
railway init
railway up

# 4. Переменные окружения
railway env

# Добавить в Railway Dashboard:
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=your-secret-key
FLASK_ENV=production
```

## FRONTEND (на Vercel)

```bash
# 1. Создать проект в Vercel
# https://vercel.com/import

# 2. Подключить GitHub
# (если хранишь там)

# 3. Деплой
npm run build
vercel

# 4. Переменные окружения
# .env.production:
REACT_APP_API_URL=https://api.alisa-letters.com
```

## ДОМЕН

```
Backend: api.alisa-letters.com
Frontend: alisa-letters.com / cabinet.alisa-letters.com
```

---

# 🎯 ГРАФИК РАЗРАБОТКИ

## НЕДЕЛЯ 1-2 (сентябрь):
```
[ ] Backend setup (Flask, SQLAlchemy, models)
[ ] Database schema
[ ] JWT аутентификация
[ ] API endpoints (базовые)
```

## НЕДЕЛЯ 3-4 (сентябрь):
```
[ ] Frontend setup (React)
[ ] Login component (Telegram)
[ ] Dashboard (дизайн + функционал)
[ ] Letter list component
```

## НЕДЕЛЯ 5 (сентябрь):
```
[ ] Letter detail (полное письмо)
[ ] PDF download
[ ] Subscription management
[ ] Testing & fixes
```

## НЕДЕЛЯ 6 (сентябрь - начало октября):
```
[ ] Telegram Bot integration
[ ] Database sync
[ ] Email notifications
[ ] Final testing
```

## 1 ОКТЯБРЯ - ЗАПУСК:
```
✅ Кабинет live
✅ Клиенты могут заходить и смотреть письма
✅ Полная синхронизация с ботом
```

---

# 🔍 ТЕСТИРОВАНИЕ

## Backend тесты

```bash
pytest tests/test_auth.py
pytest tests/test_letters.py
pytest tests/test_subscription.py
```

## Frontend тесты

```bash
npm test
npm run build
npm run test:coverage
```

## E2E тесты

```bash
# Cypress
npm install cypress
npx cypress open
```

---

# 📊 АНАЛИТИКА ДЛЯ АЛИСЫ

## Admin Panel (приватный)

```
Клиенты:
- Всего активных: 150
- Новых сегодня: 12
- Активных подписчиков: 95
- Отменили: 5

Письма:
- Отправлено: 500
- Прочитано: 480 (96%)
- В среднем читают за: 8 мин
- Избранные: 120

Доход:
- Сегодня: 25,000₽
- Месяц: 1,500,000₽
- Среднее письмо: 690₽
- Среднюю подписка: 2,800₽
```

---

# 🔒 БЕЗОПАСНОСТЬ

## Меры защиты

```
✅ HTTPS everywhere
✅ JWT токены (24 часов + refresh)
✅ CORS настроены
✅ SQL injection protection (SQLAlchemy ORM)
✅ XSS protection (React escaping)
✅ Rate limiting (на API)
✅ GDPR compliance (можно удалить данные)
✅ Шифрование пароля (если вдруг понадобится)
```

---

# 🎁 БУДУЩИЕ ФИЧИ

```
МЕСЯЦ 1:
[ ] Поделиться письмом (public link)
[ ] Экспорт в PDF
[ ] Резервная копия писем

МЕСЯЦ 2:
[ ] Рекомендации писем на основе AI
[ ] Коллекции писем (по темам)
[ ] Уведомления (Email + Push)
[ ] Social sharing (Twitter, Telegram)

МЕСЯЦ 3:
[ ] Premium фичи (расширенная аналитика)
[ ] API для интеграции
[ ] Mobile приложение
```

---

**ГОТОВО К РАЗРАБОТКЕ!** 🚀

