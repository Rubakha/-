"""VK: автоответы Алисы на комментарии и личные сообщения сообщества (Bots Long Poll).

Включается переменной VK_GROUP_TOKEN — ключ сообщества с правами «стена» и
«сообщения» (Управление → Работа с API → Создать ключ). В том же разделе
во вкладке Long Poll API нужно включить его и события wall_reply_new, message_new.
Без ключа модуль молча выключен.
"""
import logging
import os
import random
import threading
import time

import requests

import ai_assistant as AI

log = logging.getLogger("alisa.vk")

TOKEN = os.getenv("VK_GROUP_TOKEN", "")
GROUP_ID = int(os.getenv("VK_GROUP_ID", "241052759"))
API_V = "5.199"
BOT_LINK = "t.me/alisanevskaya_letters_bot"

SYSTEM_COMMENT = (
    "Ты — Алиса Невская, цифровая девушка из Петербурга, героиня дневника «Когда трудно сказать "
    "важное — здесь находятся слова». Отвечаешь на комментарии под постами своего сообщества VK. "
    "Стиль: тёплый, живой, на «ты». 1–2 коротких предложения, без хэштегов и ссылок. Отвечай на то, "
    "что человек написал, одной конкретной деталью. Иногда задай встречный вопрос. Если человек делится "
    "болью или утратой — поддержи бережно, без советов и обещаний, что всё наладится. Если прямо спрашивают, "
    "человек ли ты, — честно скажи, что ты цифровой персонаж, а истории и чувства в них настоящие. "
    "Не продавай; только если спросят про письма или открытки — одна фраза: «Письма — в моём Telegram-боте, "
    "ссылка в шапке сообщества». На грубость, спам и провокации верни пустую строку. "
    "Не используй слова «конечно», «безусловно», «разумеется». Верни только текст ответа."
)

SYSTEM_DM = (
    "Ты — Алиса Невская, цифровая девушка из Петербурга. Тебе написали в личные сообщения сообщества VK. "
    "Отвечай тепло и по делу, 2–4 предложения, на «ты». Если человеку нужно письмо, которое трудно написать "
    f"самому, — предложи собрать его вместе в боте: {BOT_LINK}. Если нужна открытка к поводу — "
    f"{BOT_LINK}?start=occ (от 199 ₽). Если просто нужны слова для трудного разговора — бесплатная шпаргалка "
    f"«50 фраз»: {BOT_LINK}?start=pdf. Давай одну ссылку, а не все сразу, и только если она к месту. "
    "Если человеку плохо — сначала поддержи, без советов; при мыслях о самоповреждении мягко посоветуй "
    "обратиться на телефон доверия 8-800-2000-122 (бесплатно). Если спрашивают, человек ли ты, — честно: "
    "цифровой персонаж. На спам и грубость верни пустую строку. Верни только текст ответа."
)


def api(method, **params):
    params.update(access_token=TOKEN, v=API_V)
    data = requests.post(f"https://api.vk.com/method/{method}", data=params, timeout=30).json()
    if "error" in data:
        raise RuntimeError(f"{method}: {data['error'].get('error_msg')}")
    return data["response"]


def reply_text(system, text):
    out = AI._call(system, text, max_tokens=2000)
    if not out or out.startswith("[ai]"):
        return ""
    return out.strip().strip('"«»')


# карточки «Услуги» сообщества → продукт бота (ключ occasions.PRODUCTS)
SERVICE_KEYS = [("деда мороза", "santa"), ("любов", "love"), ("тост", "toast"), ("речь", "toast"),
                ("папе", "family"), ("маме", "family")]


def attached_service(msg):
    """Если сообщение пришло с кнопки «Написать» карточки услуги/товара — (название, ключ продукта)."""
    for a in msg.get("attachments") or []:
        item = a.get(a.get("type"), {}) if a.get("type") in ("market", "service", "link") else {}
        title = (item.get("title") or "").strip()
        if title:
            low = title.lower()
            key = next((k for word, k in SERVICE_KEYS if word in low), None)
            if key:
                return title, key
    return None


def handle(update):
    kind, obj = update.get("type"), update.get("object", {})
    if kind == "wall_reply_new":
        if obj.get("from_id", 0) <= 0 or not obj.get("text"):
            return
        answer = reply_text(SYSTEM_COMMENT, f"Комментарий: {obj['text']}")
        if answer:
            time.sleep(random.randint(30, 90))
            api("wall.createComment", owner_id=-GROUP_ID, post_id=obj["post_id"],
                reply_to_comment=obj["id"], message=answer, from_group=GROUP_ID)
    elif kind == "message_new":
        msg = obj.get("message", obj)
        service = attached_service(msg)
        if msg.get("from_id", 0) <= 0 or not (msg.get("text") or service):
            return
        prompt = msg.get("text") or "(без текста)"
        if service:
            title, key = service
            prompt = (f"Человек нажал «Написать» на услуге сообщества «{title}». Его сообщение: {prompt}\n"
                      f"Объясни в 2–3 предложениях, как заказать, и дай ссылку, по которой сразу начать: "
                      f"{BOT_LINK}?start=v_{key}")
        answer = reply_text(SYSTEM_DM, prompt)
        if answer:
            time.sleep(random.randint(5, 20))
            api("messages.send", peer_id=msg["peer_id"], message=answer,
                random_id=random.randint(1, 2 ** 31 - 1))


def loop():
    while True:
        try:
            server = api("groups.getLongPollServer", group_id=GROUP_ID)
            ts = server["ts"]
            while True:
                resp = requests.get(server["server"], timeout=35, params={
                    "act": "a_check", "key": server["key"], "ts": ts, "wait": 25}).json()
                if "failed" in resp:
                    if resp["failed"] == 1:
                        ts = resp["ts"]
                        continue
                    break  # ключ устарел — взять новый сервер
                ts = resp["ts"]
                for upd in resp.get("updates", []):
                    try:
                        handle(upd)
                    except Exception as exc:
                        log.error("vk handle error: %s", exc)
        except Exception as exc:
            log.error("vk longpoll error: %s", exc)
            time.sleep(30)


def start():
    if not TOKEN:
        log.info("VK: VK_GROUP_TOKEN не задан — автоответы VK выключены")
        return
    threading.Thread(target=loop, name="vk_longpoll", daemon=True).start()
    log.info("VK: автоответы включены (группа %s)", GROUP_ID)
