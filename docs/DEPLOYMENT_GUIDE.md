# 🚀 РАЗВЁРТЫВАНИЕ БОТА: ШАГ ЗА ШАГОМ

**Статус:** ПОЛНАЯ ИНСТРУКЦИЯ
**Дата:** 28 августа 2026
**Цель:** Запуск бота 1 сентября 09:00 МСК

---

# 📋 СТРУКТУРА ПРОЕКТА

```
alisa_bot/
├── bot_full_code.py          # Основной код бота
├── requirements.txt           # Зависимости Python
├── .env                       # Переменные окружения (НЕ грузить на GitHub!)
├── .gitignore                 # .env, __pycache__, venv/
├── Procfile                   # Для Railway/Heroku
├── railway.toml               # Конфигурация Railway
└── README.md                  # Документация
```

---

# 1️⃣ ШАГ 1: ПОДГОТОВКА ЛОКАЛЬНО

## Создай папку проекта:

```bash
mkdir alisa_bot
cd alisa_bot
```

## Создай виртуальное окружение:

```bash
python -m venv venv

# Активируй (Mac/Linux):
source venv/bin/activate

# Активируй (Windows):
venv\Scripts\activate
```

## Установи зависимости:

```bash
pip install -r requirements.txt
```

## Создай файл `.env`:

```
TG_BOT_TOKEN=6123456789:ABCDEFghijklmnopqrst...
CLAUDE_API_KEY=sk-ant-v0-XXXxxxxxx...
GOOGLE_SHEETS_KEY={"type": "service_account", "project_id": "...", ...}
TG_CHANNEL_ID=-1001234567890
```

---

# 2️⃣ ШАГ 2: ПОЛУЧИТЬ НЕОБХОДИМЫЕ КЛЮЧИ

## A. TG_BOT_TOKEN

```
1. Напиши @BotFather в TG
2. /newbot
3. Выбери имя и юзернейм
4. Получишь TOKEN
5. Скопируй в .env
```

## B. CLAUDE_API_KEY

```
1. Перейди https://console.anthropic.com/
2. Регистрация → API Keys → Create Key
3. Скопируй: sk-ant-v0-...
4. Скопируй в .env
```

## C. GOOGLE_SHEETS_KEY

```
1. Перейди https://console.cloud.google.com/
2. Создай новый проект: "AlisaLetters"
3. Включи Google Sheets API
4. Создай Service Account (JSON ключ)
5. Скопируй весь JSON в .env

Формат:
GOOGLE_SHEETS_KEY={"type": "service_account", "project_id": "alisa-letters", ...}
```

## D. TG_CHANNEL_ID

```
1. Создай приватный канал в TG (публичный может быть и публичный)
2. Напиши в канал: @username_to_id_bot
3. Получишь ID (обычно -1001234567890)
4. Скопируй в .env
```

---

# 3️⃣ ШАГ 3: ПОДГОТОВКА GOOGLE SHEETS

## Создай таблицу "AlisaLetters":

```
1. Перейди https://sheets.google.com
2. Создай новую таблицу: "AlisaLetters"
3. Создай листы:
   - "Orders" (заказы писем)
   - "Subscriptions" (подписки)
   - "Analytics" (аналитика)
```

## Лист "Orders":

```
Колонки:
A | B | C | D | E | F | G
Дата | Username | Вопрос | Тип | Цена | Статус | Письмо
```

## Лист "Subscriptions":

```
Колонки:
A | B | C | D | E | F
Username | Тип подписки | Цена/месяц | Статус | Дата начала | Дата продления
```

## Лист "Analytics":

```
Колонки:
A | B | C | D
Дата | Тип события | Данные | День
```

---

# 4️⃣ ШАГ 4: ТЕСТИРОВАНИЕ ЛОКАЛЬНО

## Запусти бот:

```bash
python bot_full_code.py
```

## Тестируй команды:

```
1. Отправь /start
2. Проверь ответ бота
3. Отправь /письмо
4. Проверь кнопки
5. Выбери подписку
6. Проверь информацию о цене
```

## Проверь логирование:

```
1. Открой Google Sheets "AlisaLetters"
2. Перейди на лист "Analytics"
3. Должны быть новые строки (events логируются)
```

---

# 5️⃣ ШАГ 5: РАЗВЁРТЫВАНИЕ НА RAILWAY

## Установи Railway CLI:

```bash
npm install -g @railway/cli
```

## Логинься в Railway:

```bash
railway login
```

## Создай Procfile:

```
worker: python bot_full_code.py
```

## Создай railway.toml:

```toml
[build]
builder = "dockerfile"

[deploy]
startCommand = "python bot_full_code.py"
```

## Загрузи проект:

```bash
railway init
railway up
```

## Добавь переменные окружения в Railway:

```
Dashboard → Variables:
- TG_BOT_TOKEN=...
- CLAUDE_API_KEY=...
- GOOGLE_SHEETS_KEY=...
- TG_CHANNEL_ID=...
```

---

# 6️⃣ ШАГ 6: СОЗДАНИЕ GOOGLE FORM

## Для разовых писем:

```
1. Перейди https://forms.google.com
2. Создай форму "Заказ письма от Алисы"
3. Вопросы:
   - "Твоё имя или ник" (text)
   - "Твой вопрос" (long text) ⭐ ВАЖНО
   - "Формат письма" (multiple choice: Письмо/Дневник/Сценарий)
   - "Анонимно ли публиковать?" (yes/no)

4. Подключи Google Sheets:
   Responses → Select a destination → Google Sheets
   Создай лист "FormResponses"

5. Получи ссылку на форму
6. Вставь в код бота (где "YOUR_FORM_ID")
```

---

# 7️⃣ ШАГ 7: ФИНАЛЬНЫЙ ЧЕК-ЛИСТ ДО 1 СЕНТЯБРЯ

```
✅ ВСЕ КЛЮЧИ ПОЛУЧЕНЫ:
   [ ] TG_BOT_TOKEN
   [ ] CLAUDE_API_KEY
   [ ] GOOGLE_SHEETS_KEY
   [ ] TG_CHANNEL_ID

✅ НАСТРОЙКИ ГОТОВЫ:
   [ ] .env файл создан
   [ ] Google Sheets "AlisaLetters" создана
   [ ] Все листы (Orders, Subscriptions, Analytics) готовы
   [ ] Google Form создана и подключена к Sheets

✅ КОД ГОТОВ:
   [ ] bot_full_code.py загружен
   [ ] requirements.txt готов
   [ ] Локальное тестирование пройдено

✅ RAILWAY ГОТОВ:
   [ ] Проект развёрнут на Railway
   [ ] Переменные окружения добавлены
   [ ] Бот запущен и слушает команды

✅ КАНАЛ ГОТОВ:
   [ ] Канал в TG создан
   [ ] Тестовый пост отправлен
   [ ] Автопубликация готова

✅ ОБЪЯВЛЕНИЯ ГОТОВЫ:
   [ ] Стартовый пост написан
   [ ] Уведомление о интро-цене готово
   [ ] Примеры писем готовы
```

---

# 🚨 ПРОБЛЕМЫ И РЕШЕНИЯ

## Проблема 1: "TeleBot error: API key not found"

```
❌ TOKEN не скопирован правильно

✅ Решение:
1. Скопируй TOKEN заново с @BotFather
2. Убедись, что нет пробелов в начале/конце
3. Перезагрузи Railway
```

## Проблема 2: "Anthropic API error: Invalid key"

```
❌ CLAUDE_API_KEY неправильный

✅ Решение:
1. Скопируй ключ с https://console.anthropic.com/
2. Убедись, что начинается на "sk-ant-v0-"
3. Не должно быть пробелов
```

## Проблема 3: "Google Sheets не обновляется"

```
❌ Service Account не имеет доступа к Sheets

✅ Решение:
1. Открой Google Sheets "AlisaLetters"
2. Нажми "Share"
3. Вставь email из JSON ключа
4. Дай полный доступ (edit)
```

## Проблема 4: "Бот не отправляет сообщения"

```
❌ Railway не запущен или бот упал

✅ Решение:
1. railway logs (посмотри логи)
2. Проверь, есть ли ошибки в коде
3. Перезагрузи: railway up
```

---

# 📱 ТЕСТИРОВАНИЕ ПЕРЕД 1 СЕНТЯБРЯ

## День 29 августа:

```
[ ] Тестирую /start
[ ] Тестирую /письмо
[ ] Тестирую выбор подписки
[ ] Тестирую информацию о цене
[ ] Проверяю, что логирование работает
[ ] Проверяю, что автопубликация работает
```

## День 30 августа:

```
[ ] Финальная проверка всех команд
[ ] Проверка цен (сентябрь = интро)
[ ] Проверка Google Sheets логирования
[ ] Тестовый пост в канал
[ ] Всё готово!
```

## День 1 сентября (09:00):

```
🚀 ЗАПУСК!

09:00 - Первый пост выходит автоматом
09:15 - Проверяю метрики
10:00 - Вторая волна поста
18:00 - Вечернее письмо
20:00 - Первый отчёт о дне 1
```

---

# 💡 ПОЛЕЗНЫЕ КОМАНДЫ

## Railway:

```bash
railway logs              # Посмотреть логи
railway up               # Развернуть/обновить
railway down             # Остановить
railway env              # Просмотреть переменные
```

## Git (если используешь):

```bash
git init
git add .
git commit -m "Initial commit"
git push heroku main     # Если используешь Heroku
```

## Python (локально):

```bash
python bot_full_code.py              # Запуск
python -m pytest test_bot.py         # Тестирование
pip freeze > requirements.txt        # Обновить зависимости
```

---

# 🎯 ФИНАЛЬНЫЙ ЧЕКЛИСТ

```
✅ Структура папки готова
✅ Все ключи получены
✅ .env файл создан (не грузить на GitHub!)
✅ requirements.txt готов
✅ bot_full_code.py готов
✅ Google Sheets готова
✅ Google Form готова
✅ Railway готов
✅ Локальное тестирование пройдено
✅ Объявления написаны
✅ Запуск запланирован на 1 сентября 09:00

🚀 ВСЁ ГОТОВО!
```

---

**Что-то не понимаешь? Пиши, помогу разобраться!** 🤝
