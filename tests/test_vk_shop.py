"""Покупка в сообщениях VK без сети: каталог → анкета → превью → ЮKassa → выдача → веб-конверт.
Запуск: python tests/test_vk_shop.py"""
import json
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
os.environ["YOOKASSA_RECEIPT"] = ""
os.environ["DATA_DIR"] = tempfile.mkdtemp()
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["VK_GROUP_TOKEN"] = "test"

import bot_best as B  # noqa: E402
import vk_bridge as VB  # noqa: E402
import vk_shop as S  # noqa: E402

TG = []
for m in ["send_message", "send_photo", "send_chat_action", "answer_callback_query"]:
    setattr(B.bot, m, lambda *a, _m=m, **k: TG.append((_m, a, k)) or pytypes.SimpleNamespace(message_id=1))

VK = []


def fake_vk(method, **p):
    VK.append((method, p))
    if method == "photos.getMessagesUploadServer":
        return {"upload_url": "https://upload.vk/x"}
    if method == "photos.saveMessagesPhoto":
        return [{"owner_id": -1, "id": 7, "access_key": "k"}]
    if method == "users.get":
        return [{"first_name": "Аня", "last_name": "Тест"}]
    if method == "utils.getShortLink":
        return {"short_url": "https://vk.cc/abc"}
    return 1


VB.api = fake_vk
VB.time.sleep = lambda s: None
S.requests.post = lambda *a, **k: pytypes.SimpleNamespace(json=lambda: {"photo": "p", "server": 1, "hash": "h"})
S.AI.generate_occasion = lambda brief, key, qa, tone, sign, title: {
    "letter": "Папа, помнишь, как ты учил меня кататься на велосипеде? " * 10 + f"\n{sign}",
    "card_title": title, "card_line": "Спасибо, что был рядом."}
PAY = {"status": "pending", "paid": False}


def fake_yk(method, url, payload=None, idem=None):
    if method == "POST":
        assert payload["confirmation"]["return_url"] == S.RETURN_URL
        return {"id": "yk-vk", "confirmation": {"confirmation_url": "https://yoomoney.ru/pay/yk-vk"}}
    return {"id": "yk-vk", "status": PAY["status"], "paid": PAY["paid"], "amount": {"value": "199.00"}}


B.yk_request = fake_yk
S.init(B.vk_shop_deps())
assert VB.SHOP is S

PEER = 777


def say(text="", payload=None, attachments=None):
    msg = {"from_id": PEER, "peer_id": PEER, "text": text}
    if payload:
        msg["payload"] = json.dumps(payload)
    if attachments:
        msg["attachments"] = attachments
    VB.handle({"type": "message_new", "object": {"message": msg}})


def last_text():
    return [p for m, p in VK if m == "messages.send"][-1]["message"]


def last_kb():
    return json.loads([p for m, p in VK if m == "messages.send"][-1].get("keyboard", "{}"))


say("Начать", {"command": "start"})
assert "Выбери повод" in last_text() and len(last_kb()["buttons"]) == 5

# кнопка «Написать» на карточке услуги сразу открывает продукт
say("", attachments=[{"type": "market", "market": {"title": "Письмо папе или маме с открыткой"}}])
assert "199 ₽" in last_text() and json.loads(last_kb()["buttons"][0][0]["action"]["payload"]) == {"c": "go", "k": "family"}

say("✍️ Начать", {"c": "go", "k": "family"})
qs = S.questions("family")
for qkey, _ in qs:
    if qkey == "tone":
        say("🌿 Просто, без пафоса", {"c": "tone", "t": "simple"})
    else:
        say({"name": "Пап", "sign": "Серёжа"}.get(qkey, "Учил кататься на велосипеде и чинить всё на свете"))
assert S.STATES[PEER]["step"] == "pay", S.STATES[PEER]
assert any(m == "messages.send" and p.get("attachment") == "photo-1_7_k" for m, p in VK), "нет превью открытки"
assert "Целиком — 199 ₽" in json.dumps(last_kb(), ensure_ascii=False)

say("🔓 Целиком — 199 ₽", {"c": "buy"})
order_id = S.STATES[PEER]["order_id"]
order = B.get_order(order_id)
assert order["channel"] == "vk" and order["chat_id"] == "vk777" and order["yk_payment_id"] == "yk-vk"
pay_btn = last_kb()["buttons"][0][0]["action"]
assert pay_btn["type"] == "open_link" and pay_btn["link"] == "https://yoomoney.ru/pay/yk-vk"
assert any(m == "send_message" and "Заказ создан" in a[1] for m, a, k in TG), "админ не узнал о заказе"

say("✅ Я оплатил(а)", {"c": "chk", "o": order_id})
assert "пока не поступила" in last_text()

PAY.update(status="succeeded", paid=True)
B.yk_check_order(order_id)
order = B.get_order(order_id)
assert order["status"] == "done" and PEER not in S.STATES
texts = [p["message"] for m, p in VK if m == "messages.send"]
assert any("Оплата прошла" in t for t in texts) and any("велосипеде" in t for t in texts)
assert "https://vk.cc/abc" in last_text(), last_text()
assert not any(m in ("send_photo",) for m, a, k in TG), "VK-заказ ушёл в Telegram"

# веб-конверт: превью ссылки ботом VK не считается вскрытием, человек — считается
c = B.app.test_client()
code = order["gift_code"]
assert c.get(f"/e/{code}").status_code == 200
c.get(f"/e/{code}/open", headers={"User-Agent": "Mozilla/5.0 (compatible; vkShare; +http://vk.com/dev/Share)"})
assert not B.get_order(order_id).get("opened_at")
r = c.get(f"/e/{code}/open", headers={"User-Agent": "Mozilla/5.0 (iPhone)"})
assert r.status_code == 200 and "велосипеде" in r.get_data(as_text=True)
assert B.get_order(order_id)["opened_at"] and "открыл(а)" in last_text()
assert c.get(f"/e/{code}.jpg").headers["Content-Type"] == "image/jpeg"
assert c.get("/e/nope").status_code == 404

# обычный разговор по-прежнему уходит Алисе
S.AI._call = lambda system, text, max_tokens=0: "Привет! Как ты?"
say("привет, как дела")
assert last_text() == "Привет! Как ты?"

stats = B.bot_stats()
assert stats["sources"].get("vk_dm") == 1 and stats["paid_total"] == 1, stats
print("OK: vk shop")
