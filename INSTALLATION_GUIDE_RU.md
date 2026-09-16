## 🚀 ИНСТРУКЦИЯ ПО УСТАНОВКЕ FREE MODE

Архив содержит переделанный бот с полной интеграцией функции управления бесплатным режимом.

---

## 📦 ЧТО В АРХИВЕ

```
bot_upgraded/
├── bot_best.py                    ← Переделанный основной файл бота
├── free_mode_module.py            ← Модуль управления Free Mode
├── FREE_MODE_SETUP.md             ← Полная документация
├── QUICK_START.md                 ← Быстрый старт
├── backend/                       ← Папка для бэкенда (если нужен)
├── data/                          ← Папка для данных
└── docs/                          ← Папка для документации
```

---

## ⚡ БЫСТРАЯ УСТАНОВКА (3 ШАГА)

### Шаг 1: Распакуйте архив

```bash
unzip bot_upgraded_final.zip
cd bot_upgraded
```

### Шаг 2: Скопируйте файлы в ваш проект

```bash
# Замените старый bot_best.py на новый
cp bot_best.py /path/to/your/alisa_bot_package/

# Добавьте модуль Free Mode
cp free_mode_module.py /path/to/your/alisa_bot_package/
```

**Где `/path/to/your/alisa_bot_package/` — это путь к папке с вашим ботом.**

Пример:
```bash
cp bot_best.py ~/Projects/alisa_bot_package/
cp free_mode_module.py ~/Projects/alisa_bot_package/
```

### Шаг 3: Перезагрузите бот

```bash
cd ~/Projects/alisa_bot_package/
python start_bot.py
```

✅ **Готово! Бот запущен с функцией Free Mode**

---

## 🎮 ИСПОЛЬЗОВАНИЕ В TELEGRAM

### Команда администратора

Отправьте боту:
```
/free_mode_admin
```

Откроется меню:
```
⭐ Управление бесплатным режимом:

✅ Включить Free Mode
❌ Выключить Free Mode
ℹ️ Статус Free Mode
```

### Сценарий 1: Включить Free Mode для всех на 7 дней

1. `/free_mode_admin`
2. Нажмите `✅ Включить Free Mode`
3. Нажмите `👥 Всем`
4. Нажмите `7 дней`

✅ Все пользователи получат Free Mode

**Сообщение в чате:**
```
✅ Free Mode включен для 2213 пользователей

📅 На период: 7 дней
⏰ До: 16.09.2026 11:22
```

### Сценарий 2: Включить для конкретного пользователя

1. `/free_mode_admin`
2. Нажмите `✅ Включить Free Mode`
3. Нажмите `👤 Выбранному пользователю`
4. Введите ID пользователя (число, например: `123456789`)
5. Выберите период (например: `30 дней`)

✅ Пользователь получит:
- Сообщение в боте: "🎁 Поздравляем! У вас активирован бесплатный режим!"
- Free Mode активирован на 30 дней

### Сценарий 3: Выключить Free Mode

1. `/free_mode_admin`
2. Нажмите `❌ Выключить Free Mode`

✅ Free Mode выключен для всех пользователей

### Сценарий 4: Проверить статус

1. `/free_mode_admin`
2. Нажмите `ℹ️ Статус Free Mode`

**Ответ:**
```
ℹ️ Статус Free Mode:

👥 Всего пользователей: 2213
🎁 С активным Free Mode: 1823
📊 Процент: 82.4%
```

---

## 💻 ИСПОЛЬЗОВАНИЕ В КОДЕ

### Проверить, активен ли Free Mode

```python
import free_mode_module as FM

# Получить профиль пользователя
profile = get_client(chat_id)

# Проверить статус
if FM.is_free_mode_active(profile):
    print("✅ Free Mode активен!")
    # Дать доступ без ограничений
else:
    print("❌ Free Mode не активен")
    # Проверить подписку/платеж
```

### Включить Free Mode программно

```python
import free_mode_module as FM

profile = get_client(chat_id)

# Включить на 14 дней
profile = FM.enable_free_mode(profile, days=14)

# Сохранить в БД
write_json(client_path(chat_id), profile)

print("✅ Free Mode включен на 14 дней")
```

### Выключить Free Mode

```python
import free_mode_module as FM

profile = get_client(chat_id)

# Выключить
profile = FM.disable_free_mode(profile)

# Сохранить
write_json(client_path(chat_id), profile)
```

### Получить информацию

```python
import free_mode_module as FM

profile = get_client(chat_id)
info = FM.get_free_mode_info(profile)

print(f"Активен: {info['active']}")
print(f"До: {info['until']}")

# Вывод:
# Активен: True
# До: 2026-12-31T23:59:59+00:00Z
```

---

## 📝 ПРИМЕРЫ ИНТЕГРАЦИИ

### Пример 1: Проверка перед отправкой результата

```python
@bot.message_handler(commands=['get_result'])
def handle_get_result(message):
    profile = get_client(message.from_user.id)
    
    # Проверяем Free Mode
    if FM.is_free_mode_active(profile):
        # Отправить бесплатно
        send_result(message.chat.id)
    else:
        # Запросить оплату
        request_payment(message.chat.id)
```

### Пример 2: Автоматическое уведомление об истечении

```python
def check_expiring_free_modes():
    """Проверить, когда заканчивается Free Mode"""
    if not os.path.isdir(CLIENTS_DIR):
        return
    
    tomorrow = datetime.utcnow() + timedelta(days=1)
    
    for fname in os.listdir(CLIENTS_DIR):
        if fname.endswith(".json"):
            chat_id = int(fname.replace(".json", ""))
            profile = get_client(chat_id)
            
            if profile:
                info = FM.get_free_mode_info(profile)
                if info['active'] and info['until']:
                    try:
                        until = datetime.fromisoformat(
                            info['until'].replace('Z', '+00:00')
                        )
                        
                        # Если заканчивается завтра
                        if until < tomorrow:
                            bot.send_message(
                                chat_id,
                                "⚠️ Ваш Free Mode заканчивается завтра!"
                            )
                    except:
                        pass
```

### Пример 3: Разные цены для Free Mode

```python
def get_price(chat_id, format_name):
    """Получить цену в зависимости от Free Mode"""
    profile = get_client(chat_id)
    
    if FM.is_free_mode_active(profile):
        # Бесплатно!
        return 0
    else:
        # Обычная цена
        return PRICES_RUB['full'][format_name]
```

---

## 🔍 ПРОВЕРКА УСТАНОВКИ

### Проверка 1: Файлы на месте

```bash
ls -la /path/to/alisa_bot_package/bot_best.py
ls -la /path/to/alisa_bot_package/free_mode_module.py
```

Оба файла должны существовать.

### Проверка 2: Импорт модуля

```bash
cd /path/to/alisa_bot_package/
python -c "import free_mode_module; print('✅ Модуль loaded')"
```

Должно вывести: `✅ Модуль loaded`

### Проверка 3: Команда в боте

1. Отправьте `/free_mode_admin`
2. Должно появиться меню

Если не появилось:
- Проверьте, что ваш ID совпадает с `ADMIN_ID` в `.env`
- Перезагрузите бот
- Посмотрите логи в консоли

---

## ❌ РЕШЕНИЕ ПРОБЛЕМ

### Ошибка: "No module named 'free_mode_module'"

**Решение:**
- Проверьте, что файл `free_mode_module.py` находится в одной папке с `bot_best.py`
- Перезагрузите бот

```bash
ls free_mode_module.py  # Должен найти файл
```

### Ошибка: Команда `/free_mode_admin` не отвечает

**Решение:**
- Проверьте ADMIN_ID в `.env`:
  ```bash
  grep ADMIN_ID .env
  ```
- Убедитесь, что это ваш Telegram ID (число)
- Обновите `.env` если нужно:
  ```bash
  echo "ADMIN_ID=123456789" >> .env
  ```

### Ошибка: Free Mode не сохраняется

**Решение:**
- Проверьте папку `data/clients/`:
  ```bash
  ls -la data/clients/ | head
  ```
- Убедитесь, что папка существует и содержит JSON файлы
- Проверьте права доступа:
  ```bash
  chmod 755 data/clients/
  ```

### Ошибка: Дата некорректна

**Решение:**
- Проверьте часовой пояс сервера:
  ```bash
  date -R  # должно быть UTC или ваша зона
  ```
- Free Mode хранится в UTC, автоматически конвертируется

---

## 📚 ДОКУМЕНТАЦИЯ

- **FREE_MODE_SETUP.md** — подробная документация
- **QUICK_START.md** — краткий старт
- **Этот файл** — инструкция по установке

---

## 🆘 НУЖНА ПОМОЩЬ?

1. Читайте логи при запуске бота
2. Проверьте структуру файлов
3. Убедитесь, что `ADMIN_ID` правильный
4. Перезагрузите бот
5. Проверьте консоль на ошибки

---

**Версия:** 1.0  
**Дата:** 2026-09-09  
**Статус:** ✅ Ready to use
