"""Тестовый режим владельца (TEST_USERS): оплата 0 ₽ и исключение из статистики/рассылки.
Запуск: python tests/test_test_mode.py"""
import os
import sys
import tempfile
import types as pytypes

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("TG_BOT_TOKEN", "123:TEST")
os.environ["ADMIN_ID"] = "1"
os.environ["TEST_USERS"] = "777"
os.environ["YOOKASSA_PROVIDER_TOKEN"] = ""
os.environ["YOOKASSA_SHOP_ID"] = "test-shop"
os.environ["YOOKASSA_SECRET_KEY"] = "test-key"
os.environ["DATA_DIR"] = tempfile.mkdtemp()
os.environ["ANTHROPIC_API_KEY"] = ""

import bot_best as B  # noqa: E402

SENT = []


def rec(name):
    def f(*a, **k):
        SENT.append((name, a, k))
        return pytypes.SimpleNamespace(message_id=len(SENT), chat=pytypes.SimpleNamespace(id=1))
    return f


for m in ["send_message", "send_photo", "send_invoice", "send_chat_action", "answer_callback_query",
          "edit_message_text", "edit_message_reply_markup", "send_media_group", "send_document"]:
    setattr(B.bot, m, rec(m))
B.bot.register_next_step_handler = lambda *a: None
B.yk_request = lambda *a, **k: (_ for _ in ()).throw(AssertionError("ЮKassa не должна вызываться для теста"))


def user(chat):
    return pytypes.SimpleNamespace(id=chat, first_name="Тест", last_name="", username="u%d" % chat)


def msg(text, chat):
    return pytypes.SimpleNamespace(chat=pytypes.SimpleNamespace(id=chat), text=text, content_type="text",
                                   from_user=user(chat))


def call(data, chat, from_id=None):
    return pytypes.SimpleNamespace(id="c", data=data, from_user=user(from_id or chat),
                                   message=pytypes.SimpleNamespace(chat=pytypes.SimpleNamespace(id=chat),
                                                                   message_id=1))


def make_order(chat):
    B.cmd_start(msg("/start", chat))
    order = {"order_id": B.new_order_id(), "chat_id": chat, "name": "Тест", "username": "t",
             "pain": "breakup", "answers": ["a"], "mirror_text": "m", "letter_text": "Письмо целиком.",
             "price_rub": 299, "status": "pending", "is_gift": False, "gift_for": None,
             "created_at": B.now_msk().isoformat(), "paid_at": None, "delivered_at": None,
             "email": None, "rating": None}
    B.save_order(order)
    return order


assert B.is_test_user(777) and not B.is_test_user(500) and not B.is_test_user(0)

# тестовый аккаунт: кнопка 0 ₽ вместо ЮKassa
t = make_order(777)
assert B.send_order_invoice(777, t) is True
btns = [b.callback_data for b in SENT[-1][2]["reply_markup"].keyboard[0]]
assert btns == [f"test:pay:{t['order_id']}"], btns
assert B.get_order(t["order_id"])["price_rub"] == 0 and B.get_order(t["order_id"])["is_test"]

# чужой / обычный пользователь не может нажать тестовую оплату
B.test_pay(call(f"test:pay:{t['order_id']}", 777, from_id=500))
assert B.get_order(t["order_id"])["status"] == "pending"

B.test_pay(call(f"test:pay:{t['order_id']}", 777))
done = B.get_order(t["order_id"])
assert done["status"] == "done" and done["price_rub"] == 0 and done["is_test"]
assert any("Письмо целиком." in str(s[1]) + str(s[2]) for s in SENT), "письмо доставлено"

# обычный клиент: тест-кнопки нет, заказ не помечен; test:pay для его заказа не работает
r = make_order(500)
SENT.clear()
try:
    B.send_order_invoice(500, r)
except AssertionError:
    pass  # дошли до ЮKassa — это и нужно (fake_api падает)
assert not B.get_order(r["order_id"]).get("is_test")
B.test_pay(call(f"test:pay:{r['order_id']}", 500))
assert B.get_order(r["order_id"])["status"] == "pending"

# статистика, рассылка и кабинет
ids = [o["order_id"] for o in B.all_orders()]
assert t["order_id"] not in ids and r["order_id"] in ids
assert t["order_id"] in [o["order_id"] for o in B.all_orders(include_test=True)]
assert t["order_id"] in [o["order_id"] for o in B.client_orders(777)]
files = B.client_files()
assert "777.json" not in files and "500.json" in files

# админ включает тест по нику командой — без переменной окружения и рестарта
B.cmd_start(msg("/start", 888))
assert not B.is_test_user(888)
B.cmd_test_users(msg("/test_add u888", 1))
assert B.is_test_user(888) and 888 in B.read_json(B.TEST_USERS_FILE, [])
B.cmd_test_users(msg("/test_add u888", 500))  # не админ — игнор
B.TEST_USERS.discard(555)
B.cmd_test_users(msg("/test_add nobody", 1))
assert "нет среди клиентов" in [s for s in SENT if s[0] == "send_message"][-1][1][1]
B.cmd_test_users(msg("/test_off u888", 1))
assert not B.is_test_user(888) and 888 not in B.read_json(B.TEST_USERS_FILE, [])
B.cmd_test_users(msg("/test_add u1", 1))  # профиль админа не делаем тестовым
assert not B.is_test_user(1)
print("OK: тестовый режим")
