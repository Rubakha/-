"""VK-магазин «Писем с открыткой»: заказ, оплата и получение прямо в сообщениях сообщества.

Путь покупателя: «Каталог» (или кнопка «Написать» на карточке услуги) → повод → 4–6 вопросов →
превью открытки и начала письма → «Оплатить» (страница ЮKassa открывается из VK) → после оплаты
письмо, чистая открытка и ссылка-конверт приходят в тот же чат.

Хранилище заказов и ЮKassa — общие с Telegram-ботом: bot_best передаёт их через init(deps).
Заказ VK отличается полями channel="vk" и chat_id="vk<id>" (строка — не пересекается с Telegram).
"""
import json
import logging
import os
import random
import threading

import requests

import ai_assistant as AI
import occasions as OCC
import postcards
import vk_bridge as VB

log = logging.getLogger("alisa.vk_shop")

D = None                 # зависимости от bot_best (см. init)
STATES = {}              # peer_id → состояние анкеты
LOCKS = {}
LOCKS_GUARD = threading.Lock()
RETURN_URL = "https://vk.me/alisanevskaya_diary"
START_WORDS = ("начать", "каталог", "меню", "письмо", "письма", "открытк", "заказ", "купить", "start")


def init(deps):
    """deps: save_order, get_order, new_order_id, now_msk, yk_create(order, email, return_url) → url,
    yk_check(order_id) → статус, receipt_required, notify_new(order), envelope_url(order) → url, data_dir."""
    global D
    D = deps
    VB.SHOP = __import__(__name__)


def peer_lock(peer):
    with LOCKS_GUARD:
        return LOCKS.setdefault(peer, threading.Lock())


# ── отправка ─────────────────────────────────────────────────

def btn(label, payload, color="secondary"):
    return {"action": {"type": "text", "label": label[:40], "payload": json.dumps(payload)}, "color": color}


def link_btn(label, url):
    return {"action": {"type": "open_link", "label": label[:40], "link": url}}


def keyboard(rows, inline=True):
    return json.dumps({"inline": inline, "buttons": rows} if inline else
                      {"one_time": False, "buttons": rows}, ensure_ascii=False)


def send(peer, text, rows=None, attachment=None):
    params = {"peer_id": peer, "message": text, "random_id": random.randint(1, 2 ** 31 - 1)}
    if rows:
        params["keyboard"] = keyboard(rows)
    if attachment:
        params["attachment"] = attachment
    try:
        return VB.api("messages.send", **params)
    except RuntimeError as exc:
        if "keyboard" not in params:
            raise
        log.error("vk keyboard rejected (%s) — шлю без кнопок", exc)
        params.pop("keyboard")
        return VB.api("messages.send", **params)


def send_long(peer, text, rows=None):
    parts, chunk = [], ""
    for para in text.split("\n"):
        if len(chunk) + len(para) + 1 > 3800:
            parts.append(chunk)
            chunk = ""
        chunk += para + "\n"
    parts.append(chunk)
    for i, part in enumerate(parts):
        send(peer, part.strip(), rows if i == len(parts) - 1 else None)


def upload_photo(peer, jpg):
    """Загружает открытку в сообщения VK; None, если у ключа нет прав на фото."""
    try:
        srv = VB.api("photos.getMessagesUploadServer", peer_id=peer)
        up = requests.post(srv["upload_url"], files={"photo": ("card.jpg", jpg, "image/jpeg")}, timeout=60).json()
        p = VB.api("photos.saveMessagesPhoto", photo=up["photo"], server=up["server"], hash=up["hash"])[0]
        return f"photo{p['owner_id']}_{p['id']}" + (f"_{p['access_key']}" if p.get("access_key") else "")
    except Exception as exc:
        log.error("vk photo upload: %s", exc)
        return None


def short(url):
    try:
        return VB.api("utils.getShortLink", url=url, private=1)["short_url"]
    except Exception:
        return url


# ── каталог ──────────────────────────────────────────────────

def show_catalog(peer):
    keys = OCC.CATALOG_ORDER[:10]
    rows = [[btn(f"{OCC.PRODUCTS[k]['icon']} {OCC.PRODUCTS[k]['title']}", {"c": "p", "k": k}, "primary")
             for k in keys[i:i + 2]] for i in range(0, len(keys), 2)]
    send(peer, "💌 Письмо с открыткой — прямо здесь, в сообщениях.\n\n"
               "Выбери повод → ответь на несколько вопросов → посмотри открытку и начало письма. "
               f"Платишь, только если нравится: от {OCC.price_from()} ₽. Письмо и открытка придут сюда же.",
         rows)


def show_product(peer, key):
    p = OCC.PRODUCTS[key]
    send(peer, f"{p['icon']} {p['title']} — {p['price']} ₽\n\n{p['pitch']}\n\n"
               "Займёт 3 минуты: ответишь на вопросы, я соберу письмо и открытку с именем. "
               "Превью — до оплаты.",
         [[btn("✍️ Начать", {"c": "go", "k": key}, "positive")], [btn("← Все поводы", {"c": "cat"})]])


def questions(key):
    p = OCC.PRODUCTS[key]
    return [(k, t) for k, t in p["questions"]
            if not (k == "tone" and p.get("tone")) and not (k == "sign" and p.get("sign"))]


def start(peer, key):
    STATES[peer] = {"step": "q", "product": key, "idx": 0, "qa": [], "data": {}}
    ask(peer)


def ask(peer):
    st = STATES[peer]
    qs = questions(st["product"])
    if st["idx"] >= len(qs):
        return finish(peer)
    st["qkey"], st["qtext"] = qs[st["idx"]]
    if st["qkey"] == "tone":
        rows = [[btn(label, {"c": "tone", "t": t}) for t, label in list(OCC.TONES.items())[i:i + 2]]
                for i in (0, 2)]
        send(peer, st["qtext"], rows)
    else:
        send(peer, f"{st['idx'] + 1}/{len(qs)}. {st['qtext']}")


def store(peer, value):
    st = STATES[peer]
    st["data"][st["qkey"]] = value
    if st["qkey"] != "tone":
        st["qa"].append((st["qtext"], value))
    st["idx"] += 1
    ask(peer)


def finish(peer):
    st = STATES[peer]
    key, p, data = st["product"], OCC.PRODUCTS[st["product"]], st["data"]
    name = data.get("name", "").strip()
    sign = p.get("sign") or data.get("sign", "").strip()
    tone = p.get("tone") or data.get("tone", "simple")
    default_title = p["card_title"].format(name=name)[:40]
    st["step"] = "gen"
    send(peer, "✍️ Пишу… это займёт около минуты.")
    res = AI.generate_occasion(p["brief"], key, st["qa"], tone, sign, default_title)
    if res["letter"].startswith("[ai]"):
        STATES.pop(peer, None)
        log.error("vk occasion generation failed: %s", res["letter"])
        return send(peer, "Не получилось написать письмо прямо сейчас 😔 Попробуй через пару минут.",
                    [[btn("Попробовать снова", {"c": "go", "k": key}, "primary")]])
    st.update(step="pay", letter=res["letter"], card_title=res["card_title"],
              card_line=res["card_line"], sign=sign, name=name)
    photo = upload_photo(peer, postcards.render(key, res["card_title"], res["card_line"], sign, preview=True))
    if photo:
        send(peer, "Твоя открытка (превью) 🖼", attachment=photo)
    letter = res["letter"]
    cut = max(220, int(len(letter) * 0.4))
    send(peer, letter[:cut].rsplit(" ", 1)[0] + "…\n\n🔒 Дальше — письмо целиком, чистая открытка "
               "без надписи «превью» и ссылка-конверт для получателя.",
         [[btn(f"🔓 Целиком — {p['price']} ₽", {"c": "buy"}, "positive")], [btn("❌ Отменить", {"c": "cancel"})]])


# ── заказ и оплата ───────────────────────────────────────────

def user_name(peer):
    try:
        u = VB.api("users.get", user_ids=peer)[0]
        return f"{u.get('first_name', '')} {u.get('last_name', '')}".strip()
    except Exception:
        return ""


def remember_client(peer):
    path = os.path.join(D.data_dir, "vk_clients", f"{peer}.json")
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"vk_id": peer, "created_at": D.now_msk().isoformat(), "source": "vk"}, f)


def buy(peer):
    st = STATES.get(peer) or {}
    if st.get("step") != "pay":
        return send(peer, "Заказ устарел — начнём заново?", [[btn("💌 Каталог", {"c": "cat"}, "primary")]])
    p = OCC.PRODUCTS[st["product"]]
    order = {
        "order_id": D.new_order_id(), "chat_id": f"vk{peer}", "vk_peer": peer, "channel": "vk",
        "name": f"{user_name(peer)} (VK)", "username": f"vk.com/id{peer}",
        "pain": st["product"], "product": st["product"],
        "answers": [a for _, a in st["qa"]], "qa": st["qa"], "mirror_text": None,
        "letter_text": st["letter"], "card_title": st["card_title"], "card_line": st["card_line"],
        "sign": st["sign"], "price_rub": p["price"], "status": "pending", "is_gift": True,
        "gift_for": st.get("name"), "created_at": D.now_msk().isoformat(),
        "paid_at": None, "delivered_at": None, "email": None, "rating": None,
    }
    D.save_order(order)
    remember_client(peer)
    D.notify_new(order)
    st.update(step="email" if D.receipt_required else "wait", order_id=order["order_id"])
    if D.receipt_required:
        return send(peer, "📧 Куда прислать чек об оплате? Напиши почту одним сообщением.")
    pay_link(peer, order)


def pay_link(peer, order, email=None):
    try:
        url = D.yk_create(order, email, RETURN_URL)
    except Exception as exc:
        log.error("vk yookassa create %s: %s", order["order_id"], exc)
        return send(peer, f"⚠️ Не смог открыть страницу оплаты. Попробуй через минуту.\nЗаказ {order['order_id']}",
                    [[btn("Ещё раз", {"c": "repay", "o": order["order_id"]}, "primary")]])
    STATES.setdefault(peer, {}).update(step="wait", order_id=order["order_id"])
    send(peer, f"Заказ {order['order_id']} · {order['price_rub']} ₽\n\n"
               "Оплата — на защищённой странице ЮKassa: СБП, SberPay, T-Pay, карта или ЮMoney.\n"
               "После оплаты письмо и открытка придут сюда сами в течение минуты 🤍",
         [[link_btn(f"💳 Оплатить {order['price_rub']} ₽", url)],
          [btn("✅ Я оплатил(а)", {"c": "chk", "o": order["order_id"]})]])


def check(peer, order_id):
    order = D.get_order(order_id)
    if not order or order.get("vk_peer") != peer:
        return send(peer, "Заказ не найден.")
    if order.get("status") == "done":
        return
    try:
        status = D.yk_check(order_id)
    except Exception as exc:
        log.error("vk yookassa check %s: %s", order_id, exc)
        status = None
    if status == "canceled":
        send(peer, "Платёж не прошёл. Можно попробовать ещё раз:",
             [[btn("💳 Оплатить снова", {"c": "repay", "o": order_id}, "primary")]])
    elif status != "succeeded":
        send(peer, "Оплата пока не поступила. Если уже оплатил(а) — подожди минуту, письмо придёт само.")


def on_paid(order):
    """Вызывается из bot_best.fulfill_order после подтверждённой оплаты."""
    peer = order["vk_peer"]
    STATES.pop(peer, None)
    send(peer, f"✅ Оплата прошла · заказ {order['order_id']}"
               + (f"\nЧек придёт на {order['email']}" if order.get("email") else ""))
    photo = upload_photo(peer, postcards.render(order["product"], order.get("card_title", ""),
                                                order.get("card_line", ""), order.get("sign", "")))
    if photo:
        send(peer, "🖼 Твоя открытка", attachment=photo)
    send_long(peer, order["letter_text"])
    link = short(D.envelope_url(order))
    send(peer, "✉️ Как подарить\n\n"
               f"1. Отправь получателю ссылку-конверт: {link}\n"
               "Он откроет её в любом браузере: сначала открытка, потом письмо. "
               "Я напишу тебе, когда конверт вскроют ✨\n\n"
               "2. Или просто перешли ему открытку и письмо выше.",
         [[btn("🎀 Ещё одно письмо", {"c": "cat"}, "primary")]])


def notify_opened(order):
    try:
        send(order["vk_peer"], f"✨ {order.get('gift_for') or 'Получатель'} только что открыл(а) твоё письмо.")
    except Exception as exc:
        log.error("vk notify opened: %s", exc)


# ── маршрутизация входящих ───────────────────────────────────

def handle_message(msg, service_key=None):
    """True — сообщение обработано магазином; False — отдать обычному автоответу Алисы."""
    if D is None:
        return False
    peer = msg.get("from_id", 0)
    with peer_lock(peer):
        return _route(peer, msg, service_key)


def _route(peer, msg, service_key):
    text = (msg.get("text") or "").strip()
    try:
        payload = json.loads(msg.get("payload") or "{}")
    except ValueError:
        payload = {}
    if payload.get("command") == "start":
        payload = {"c": "cat"}
    cmd = payload.get("c")
    st = STATES.get(peer) or {}

    if service_key:
        show_product(peer, service_key)
    elif cmd == "cat":
        STATES.pop(peer, None)
        show_catalog(peer)
    elif cmd == "p" and payload.get("k") in OCC.PRODUCTS:
        show_product(peer, payload["k"])
    elif cmd == "go" and payload.get("k") in OCC.PRODUCTS:
        start(peer, payload["k"])
    elif cmd == "tone" and st.get("step") == "q" and st.get("qkey") == "tone":
        store(peer, payload.get("t", "simple"))
    elif cmd == "buy":
        buy(peer)
    elif cmd == "cancel":
        STATES.pop(peer, None)
        send(peer, "Отменила. Если захочешь вернуться — напиши «каталог» 🤍")
    elif cmd == "chk":
        check(peer, payload.get("o", ""))
    elif cmd == "repay":
        order = D.get_order(payload.get("o", ""))
        if order and order.get("vk_peer") == peer and order.get("status") == "pending":
            pay_link(peer, order, order.get("email"))
    elif st.get("step") == "q":
        if st.get("qkey") == "tone":
            tone = next((t for t, label in OCC.TONES.items() if text and text.lower() in label.lower()), None)
            if tone:
                store(peer, tone)
            else:
                send(peer, "Выбери тон кнопкой выше 👆")
        elif not text:
            send(peer, "Напиши хотя бы пару слов 🙂")
        elif len(text) > 1500:
            send(peer, "Слишком длинно — сократи до 1500 знаков, пожалуйста.")
        else:
            store(peer, text)
    elif st.get("step") == "email":
        if "@" not in text or "." not in text.split("@")[-1] or " " in text:
            send(peer, "Не похоже на почту 🙈 Напиши, пожалуйста, в виде name@mail.ru")
        else:
            order = D.get_order(st["order_id"])
            order["email"] = text
            D.save_order(order)
            pay_link(peer, order, text)
    elif st.get("step") == "gen":
        send(peer, "Ещё пишу — минутку ✍️")
    elif text and any(w in text.lower() for w in START_WORDS) and len(text) < 40:
        show_catalog(peer)
    else:
        return False
    return True
