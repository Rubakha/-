# 🔧 ПОЛНАЯ ИНСТРУКЦИЯ: ИНТЕГРАЦИЯ CLAUDE В TG БОТ

**Статус:** ПОШАГОВАЯ ИНСТРУКЦИЯ
**Сложность:** Средняя (но я помогу)
**Время:** 30-60 минут

---

# 🎯 ЧТО МЫ ДЕЛАЕМ

```
Подписчик заполняет форму в Google Form
    ↓
Ответ сохраняется в Google Sheets
    ↓
Google Apps Script отправляет вебхук в бот
    ↓
Python бот получает данные
    ↓
BOT ОТПРАВЛЯЕТ В CLAUDE API: вопрос подписчика + промпт
    ↓
CLAUDE ГЕНЕРИРУЕТ: письмо (Письмо/Дневник/Сценарий)
    ↓
БОТ ОТПРАВЛЯЕТ ПОДПИСЧИКУ В TG: полное письмо
```

---

# 1️⃣ ШАГ 1: ПОЛУЧИТЬ API KEY CLAUDE

## Что это:
```
API ключ = ваш билет в Claude. 
Без него Claude не может работать.
```

## Как получить:

### Способ A: Через Anthropic (официально)
```
1. Перейди https://console.anthropic.com/
2. Зарегистрируйся (email + пароль)
3. Перейди в "API Keys" (левое меню)
4. Нажми "Create Key"
5. Скопируй ключ (он выглядит так: sk-ant-v0-XXXxxxxxx...)
6. СОХРАНИ ЕГО ГДЕ-НИБУДЬ БЕЗОПАСНО

⚠️ ВАЖНО: Никому не показывай этот ключ!
```

### Стоимость:
```
Claude API платная, но дешёвая:
- Письмо (400-600 слов): ~0.02-0.05$ (~2-5 рублей)
- Дневник (700-1000 слов): ~0.03-0.08$ (~3-8 рублей)
- Сценарий (1000-1500 слов): ~0.05-0.10$ (~5-10 рублей)

На 100 писем/месяц = ~5-10$ (~500-1000 рублей)
(это меньше чем комиссия платёжных систем!)
```

---

# 2️⃣ ШАГ 2: УСТАНОВИТЬ БИБЛИОТЕКУ CLAUDE

## На твоём компьютере / сервере:

```bash
pip install anthropic -q
```

## Проверить, что установилось:

```bash
python -c "import anthropic; print('OK')"
```

Если выведет "OK" = установилось правильно.

---

# 3️⃣ ШАГ 3: НАПИСАТЬ КОД ИНТЕГРАЦИИ

## Базовый пример (простой Claude запрос):

```python
from anthropic import Anthropic

# Инициализируем Claude
client = Anthropic(api_key="sk-ant-v0-XXXxxxxxx...")  # Твой API ключ

# Отправляем запрос
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",  # Модель Claude
    max_tokens=1024,  # Макс слов в ответе
    messages=[
        {
            "role": "user",
            "content": "Привет, как дела?"
        }
    ]
)

# Получаем ответ
print(message.content[0].text)
```

---

# 4️⃣ ШАГ 4: ИНТЕГРАЦИЯ С ВАШИМ ПРОМПТОМ (АЛИСА)

## Полный код интеграции Claude в TG Bot:

```python
from anthropic import Anthropic
from telebot import TeleBot
import os
from dotenv import load_dotenv

load_dotenv()

# Инициализируем Claude и TG Bot
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")  # sk-ant-v0-XXX
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")  # Твой TG токен

client = Anthropic(api_key=CLAUDE_API_KEY)
bot = TeleBot(TG_BOT_TOKEN)

# ПРОМПТ ДЛЯ CLAUDE (Алиса)
ALICE_PROMPT = """
Ты Алиса Невская.

Ты живёшь в Санкт-Петербурге и пишешь письма людям о том, что их волнует.
Ты не психолог, не коуч, не советчик.

Ты просто пишешь правду так, как её видишь.

ХАРАКТЕР:
- Честная, не боишься сказать неприятное
- Поэтичная, видишь красоту в обычных вещах
- Глубокая, думаешь о смысле жизни, времени, смерти
- Петербургская, везде в речи Петербург (каналы, Нева, архитектура)
- Странная, живёшь необычной жизнью

СТИЛЬ ПИСЬМА (для этого письма):
- Начни с прямого утверждения (может быть вызывающее)
- Переходи к лиризму и размышлениям
- Заканчивай мотивацией к действию
- Упоминай Петербург где-то в середине
- Объём: 400-600 слов

ВОПРОС ПОДПИСЧИКА:
{question}

Тип письма (если указано): {letter_type}

Напиши письмо ответ от Алисы прямо сейчас. Начни сразу с первой строки письма.
"""

# ФУНКЦИЯ: Генерация письма через Claude
def generate_letter(question, letter_type="Письмо"):
    """
    question = вопрос подписчика
    letter_type = "Письмо" / "Дневник" / "Сценарий"
    """
    
    # Форматируем промпт с вопросом подписчика
    prompt = ALICE_PROMPT.format(
        question=question,
        letter_type=letter_type
    )
    
    # Отправляем в Claude
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,  # Много слов для полного письма
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    # Извлекаем текст ответа
    letter_text = message.content[0].text
    
    return letter_text

# ФУНКЦИЯ: Обработчик команды /письмо
@bot.message_handler(commands=['письмо'])
def handle_letter_command(message):
    chat_id = message.chat.id
    
    # Отправляем форму или ссылку
    letter_text = """
📝 ЗАКАЖИ ПИСЬМО ОТ АЛИСЫ

Выбери формат:
💌 ПИСЬМО (690₽) — Короткое (400-600 слов)
📖 ДНЕВНИК (890₽) — Глубокое (700-1000 слов)
🎬 СЦЕНАРИЙ (1290₽) — Встреча в кафе (1000-1500 слов)

⬇️ Заполни форму:
[ССЫЛКА НА GOOGLE FORM]
"""
    
    bot.send_message(chat_id, letter_text)

# ФУНКЦИЯ: Обработка ответа из Google Sheets (вебхук)
@bot.message_handler(func=lambda message: message.text.startswith("claude:"))
def handle_claude_request(message):
    """
    Этот обработчик ловит сообщения вида:
    "claude:вопрос подписчика:Письмо"
    """
    chat_id = message.chat.id
    
    try:
        parts = message.text.split(":")
        question = parts[1]
        letter_type = parts[2] if len(parts) > 2 else "Письмо"
        
        # Отправляем "генерирую письмо..."
        bot.send_message(chat_id, "⏳ Алиса пишет письмо...")
        
        # Генерируем письмо через Claude
        letter = generate_letter(question, letter_type)
        
        # Отправляем письмо подписчику
        bot.send_message(chat_id, f"Вот твоё письмо:\n\n{letter}")
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {str(e)}")

# Запускаем бот
if __name__ == "__main__":
    print("✅ Бот запущен и слушает Claude запросы...")
    bot.infinity_polling()
```

---

# 5️⃣ ШАГ 5: ИНТЕГРАЦИЯ С GOOGLE SHEETS (АВТОМАТИЗАЦИЯ)

## Google Apps Script (отправляет вебхук при новом ответе):

```javascript
function onFormSubmit(e) {
  const sheet = SpreadsheetApp.getActiveSheet();
  const values = e.values;
  
  // Извлекаем данные из формы
  const timestamp = values[0];
  const username = values[1];
  const question = values[2];
  const letterType = values[3];
  const anonymous = values[4];
  
  // Данные для логирования
  const logData = {
    timestamp: timestamp,
    username: username,
    question: question,
    letterType: letterType,
    status: "pending_claude",  // Ожидает генерации Claude
    created_at: new Date()
  };
  
  // Логируем в отдельный лист "Log"
  const logSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Log");
  logSheet.appendRow([
    logData.timestamp,
    logData.username,
    logData.question,
    logData.letterType,
    logData.status,
    logData.created_at
  ]);
  
  // Отправляем вебхук в TG бот
  const webhookUrl = "https://your-bot-domain.com/webhook";  // URL твоего бота
  
  const payload = {
    chat_id: username,  // Или ID из TG
    message: `claude:${question}:${letterType}`
  };
  
  UrlFetchApp.fetch(webhookUrl, {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload)
  });
  
  Logger.log("Отправлено в Claude: " + question);
}
```

---

# 6️⃣ ШАГ 6: ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ (.env файл)

## Создай файл `.env` в папке проекта:

```
# .env файл

CLAUDE_API_KEY=sk-ant-v0-XXXxxxxxx...
TG_BOT_TOKEN=6123456789:ABCDEFghijklmnopqrst...
TG_WEBHOOK_URL=https://your-bot-domain.com/webhook
```

## Загрузи в Railway:
```
В Railway → Environment Variables:
CLAUDE_API_KEY=sk-ant-v0-...
TG_BOT_TOKEN=6123456789:ABC...
```

---

# 7️⃣ ШАГ 7: РАЗВЁРТЫВАНИЕ НА RAILWAY

## 1. Создай `requirements.txt`:

```
anthropic==0.31.1
pyTelegramBotAPI==4.14.0
python-dotenv==1.0.0
flask==3.0.0
requests==2.31.0
google-api-python-client==1.12.5
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
```

## 2. Создай `Procfile`:

```
web: python bot.py
```

## 3. Залей на Railway:

```bash
git push heroku main
# или
railway up
```

---

# 8️⃣ ШАГ 8: ТЕСТИРОВАНИЕ

## Тест 1: Claude работает?

```python
from anthropic import Anthropic

client = Anthropic(api_key="sk-ant-v0-XXX...")

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=100,
    messages=[{"role": "user", "content": "Привет"}]
)

print(response.content[0].text)
```

Должно вывести какой-то ответ от Claude.

## Тест 2: Бот работает?

```bash
python -m pytest test_bot.py
```

## Тест 3: Письмо генерируется?

Отправь боту: `/письмо`
Заполни форму
Жди ответа (это займёт 10-30 сек)

---

# 🎯 ПОЛНЫЙ ПРИМЕР: ОТ НАЧАЛА ДО КОНЦА

## Файловая структура проекта:

```
my_alice_bot/
├── bot.py              # Основной код бота
├── claude_integration.py  # Функции Claude
├── google_sheets.py    # Функции Google Sheets
├── requirements.txt    # Зависимости
├── .env               # Переменные окружения (не грузить на GitHub!)
├── Procfile           # Для Railway/Heroku
└── README.md
```

## Файл `claude_integration.py`:

```python
from anthropic import Anthropic
import os

class AliceLetterGenerator:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
        self.model = "claude-3-5-sonnet-20241022"
    
    def generate_letter(self, question, letter_type="Письмо"):
        """Генерирует письмо от Алисы"""
        
        prompts = {
            "Письмо": self._get_letter_prompt(question),
            "Дневник": self._get_diary_prompt(question),
            "Сценарий": self._get_scenario_prompt(question)
        }
        
        prompt = prompts.get(letter_type, prompts["Письмо"])
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text
    
    def _get_letter_prompt(self, question):
        return f"""
Ты Алиса Невская. Напиши личное письмо (400-600 слов) человеку, 
который написал:

"{question}"

Начни с прямого утверждения. Используй метафоры из Петербурга. 
Заканчивай мотивацией к действию. Будь честной, но поэтичной.
"""
    
    def _get_diary_prompt(self, question):
        return f"""
Ты Алиса Невская. Напиши дневник (700-1000 слов) о том, как ты 
думаешь о проблеме подписчика:

"{question}"

Это твой внутренний монолог. Используй озарения, наблюдения, 
истории из твоей цифровой жизни. Петербург как контекст.
"""
    
    def _get_scenario_prompt(self, question):
        return f"""
Ты Алиса Невская. Напиши сценарий встречи в кафе (1000-1500 слов) 
с человеком, чей вопрос:

"{question}"

Формат: диалог с ремарками. Место: кафе на Невском. 
В конце он понимает то, что не понимал в начале.
"""

# Использование:
if __name__ == "__main__":
    generator = AliceLetterGenerator()
    letter = generator.generate_letter(
        "Я не знаю, куда идти в жизни",
        "Письмо"
    )
    print(letter)
```

---

# 🚨 ОШИБКИ И РЕШЕНИЯ

## Ошибка 1: "Invalid API key"
```
❌ Скопировал неправильно ключ

✅ Решение:
1. Удали весь текст в переменной CLAUDE_API_KEY
2. Скопируй ключ заново с https://console.anthropic.com/
3. Убедись, что ключ начинается на "sk-ant-v0-"
```

## Ошибка 2: "Rate limit exceeded"
```
❌ Отправляешь слишком много запросов в Claude

✅ Решение:
1. Добавь задержку между запросами: time.sleep(2)
2. Используй очередь (Queue) для обработки запросов
3. Кэшируй часто повторяющиеся письма
```

## Ошибка 3: "Connection timeout"
```
❌ Claude API недоступна

✅ Решение:
1. Проверь интернет
2. Проверь, что сервер Railway запущен
3. Добавь retry логику:

for attempt in range(3):
    try:
        # Отправь в Claude
        break
    except Exception as e:
        if attempt < 2:
            time.sleep(2)
        else:
            raise
```

---

# 📊 ИТОГОВАЯ АРХИТЕКТУРА

```
Google Form
    ↓
Google Sheets (ответы сохраняются)
    ↓
Google Apps Script (вебхук)
    ↓
TG Bot (на Railway)
    ↓
Claude API (генерирует письмо)
    ↓
TG Bot (отправляет письмо подписчику)
    ↓
Подписчик получает письмо! ✅
```

---

# 🎯 БЫСТРЫЙ СТАРТ (5 МИНУТ)

```
1. Получи API ключ Claude: https://console.anthropic.com/
2. Скопируй код из раздела "ШАГ 4"
3. Вставь свой API ключ и TG токен
4. Запусти: python bot.py
5. Тестируй: /письмо
6. Готово!
```

---

**Всё понятно? Есть вопросы по интеграции?**

Я могу:
- Написать полный `bot.py` файл
- Помочь с развёртыванием на Railway
- Отладить ошибки
- Оптимизировать скорость

**Скажи мне, что конкретно нужно.** 🚀
