#!/usr/bin/env python
"""Тест ключа Anthropic — берёт ключ из окружения (.env), ничего не хардкодит."""
import os

from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("ANTHROPIC_API_KEY", "")

if not KEY:
    raise SystemExit("ANTHROPIC_API_KEY не задан в .env")

print("Проверяю ключ...")
print(f"Ключ длина: {len(KEY)}")
print(f"Начинается: {KEY[:20]}...")
print()

try:
    from anthropic import Anthropic
    client = Anthropic()
    resp = client.messages.create(
        model='claude-sonnet-4-5',
        max_tokens=20,
        messages=[{'role': 'user', 'content': 'Скажи одно слово: ОК'}]
    )
    print("✅ КЛЮЧ РАБОТАЕТ")
    print(f"Ответ модели: {resp.content[0].text}")
except Exception as e:
    print("❌ КЛЮЧ НЕ РАБОТАЕТ")
    msg = str(e)
    print(f"Ошибка: {msg[:300]}")
    if "authentication" in msg.lower() or "401" in msg:
        print("\n→ Ключ не принят. Проверь, что скопировал полностью без пробелов.")
    elif "credit" in msg.lower() or "balance" in msg.lower():
        print("\n→ Закончился баланс в Anthropic. Пополни в console.anthropic.com → Billing")
    elif "not_found" in msg.lower() and "model" in msg.lower():
        print("\n→ Модель claude-sonnet-4-5 недоступна. Проверь список моделей.")
