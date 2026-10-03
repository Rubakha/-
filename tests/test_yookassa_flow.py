"""Оплата через страницу ЮKassa без сети: подменяем API и методы бота.
Запуск: python tests/test_yookassa_flow.py"""
import os
import sys
import tempfile
import types as pytypes

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("TG_BOT_TOKEN", "123:TEST")
os.environ["ADMIN_ID"] = "1"
os.environ["YOOKASSA_PROVIDER_TOKEN"] = ""
os.environ["YOOKASSA_SHOP_ID"] = "test-shop"
os.environ["YOOKASSA_SECRET_KEY"] = "test-key"
os.environ["YOOKASSA_RECEIPT"] = "1"
os.environ["DATA_DIR"] = tempfile.mkdtemp()
os.environ["ANTHROPIC_API_KEY"] = ""

import bot_best as B  # noqa: E402

SENT, API, NEXT = [], [], []
PAY = {"status": "pending", "paid": False}


def rec(name):
    def f(*a, **k):
        SENT.append((name, a, k))
        return pytypes.SimpleNamespace(message_id=len(SENT), chat=pytypes.SimpleNamespace(id=500))
    return f


for m in ["send_message", "send_photo", "send_invoice", "send_chat_action", "answer_callback_query",
          "edit_message_text", "edit_message_reply_markup", "send_media_group", "send_document"]:
    setattr(B.bot, m, rec(m))
B.bot.register_next_step_handler = lambda msg, fn, *a: NEXT.append((fn, a))


def fake_api(method, url, payload=None, idem=None):
    API.append((method, url, payload))
    if method == "POST":
        assert payload["receipt"]["customer"]["email"] == "a@b.ru"
        return {"id": "yk-1", "confirmation": {"confirmation_url": "https://yoomoney.ru/pay/yk-1"}}
    return {"id": "yk-1", "status": PAY["status"], "paid": PAY["paid"],
            "amount": {"value": PAY.get("value", "199.00"), "currency": "RUB"}}


B.yk_request = fake_api


class FakeAI:
    @staticmethod
    def available():
        return True

    @staticmethod
    def generate_occasion(brief, key, qa, tone, sign, title):
        return {"letter": "Катя, помнишь черешню на крыше? " * 12 + f"\n{sign}",
                "card_title": title, "card_line": "Ты смеёшься громче всех."}


B.AI = FakeAI


def msg(text, chat=500):
    return pytypes.SimpleNamespace(chat=pytypes.SimpleNamespace(id=chat), text=text, content_type="text",
                                   from_user=pytypes.SimpleNamespace(id=chat, first_name="Тест", last_name="",
                                                                     username="t"))


def call(data, chat=500):
    return pytypes.SimpleNamespace(id="c", data=data, from_user=msg("", chat).from_user,
                                   message=pytypes.SimpleNamespace(chat=pytypes.SimpleNamespace(id=chat),
                                                                   message_id=1))


B.cmd_start(msg("/start occ"))
B.occ_go(call("occ:go:birthday"))
for a in ["Катя", "подруга", "30", "черешня на крыше"]:
    B.occ_answer(msg(a))
B.occ_tone(call("occ:tone:warm"))
B.occ_answer(msg("Серёжа"))
B.occ_buy(call("occ:buy"))

assert not any(s[0] == "send_invoice" for s in SENT), "ушли во встроенную оплату Telegram"
fn, args = NEXT.pop()                       # бот спросил почту для чека
fn(msg("не почта"), *args)                  # неверная — переспрашивает
fn, args = NEXT.pop()
fn(msg("a@b.ru"), *args)
order_id = args[0]
order = B.get_order(order_id)
assert order["yk_payment_id"] == "yk-1" and order["email"] == "a@b.ru", order
btn = [s for s in SENT if s[0] == "send_message" and "ЮKassa" in s[1][1]][-1][2]["reply_markup"]
assert btn.keyboard[0][0].url.startswith("https://yoomoney.ru/pay/")

B.yk_check_button(call("yk:check:" + order_id))          # ещё не оплачено
assert B.get_order(order_id)["status"] == "pending"

PAY.update(status="succeeded", paid=True, value="1.00")   # сумма не совпала — не выдаём
B.yk_check_order(order_id)
assert B.get_order(order_id)["status"] == "pending"

PAY["value"] = "199.00"
B.yk_check_order(order_id)
order = B.get_order(order_id)
assert order["status"] == "done" and order["charge_id"] == "yk-1" and order.get("gift_code"), order
n = len(SENT)
B.yk_check_order(order_id)                                # повторная проверка не выдаёт второй раз
assert len(SENT) == n
print("OK: yookassa flow checks passed,", len(API), "api calls")
