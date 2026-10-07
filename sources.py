"""Отчёт по источникам: источник -> старты -> превью -> оплаты -> выручка за 7/30 дней.

Источник клиента — метка первого захода (first touch) из /start: ig_<тема>, vk_<тема>, yt_<тема>,
pin_<тема>, tg_<тема>, ad_<канал>, vkads_<повод>, p_<код>, а также gift/ref/group/web/vk/pdf/occ.
Старт = новый клиент за период; превью = клиент, которому показали превью письма (Telegram-сценарии);
оплата = заказ со статусом done и ценой > 0 (источник — из заказа, иначе из профиля клиента).
Подключается из bot_best: sources.register(bot_best).
"""
import os
from datetime import timedelta

import cardbase

B = None


def _client_sources():
    out = {}
    for fname in B.client_files():
        c = B.read_json(os.path.join(B.CLIENTS_DIR, fname), None) or {}
        if c.get("chat_id") is not None:
            out[c["chat_id"]] = (c.get("source") or "unknown", c.get("created_at", ""))
    return out


def _anketa_preview_chats(since_iso):
    chats = set()
    adir = B.ANKETAS_DIR
    for fname in os.listdir(adir) if os.path.isdir(adir) else []:
        a = B.read_json(os.path.join(adir, fname), None) or {}
        if a.get("letter_text") and a.get("created_at", "") >= since_iso and a.get("chat_id"):
            chats.add(a["chat_id"])
    return chats


def report(days, now=None):
    """Возвращает список строк по источникам (по убыванию выручки) и итог."""
    now = now or B.now_msk()
    since = (now - timedelta(days=days)).isoformat()
    clients = _client_sources()
    rows = {}

    def row(src):
        return rows.setdefault(src, {"source": src, "starts": 0, "previews": 0, "paid": 0, "revenue": 0})

    for src, created in clients.values():
        if created >= since:
            row(src)["starts"] += 1
    try:
        preview_ids = cardbase.preview_chats(days)
    except Exception:
        preview_ids = set()
    preview_ids |= _anketa_preview_chats(since)
    for chat_id in preview_ids:
        if chat_id in clients and not B.is_test_user(chat_id):
            row(clients[chat_id][0])["previews"] += 1
    for o in B.all_orders():
        if o.get("status") != "done" or o.get("price_rub", 0) <= 0 or o.get("refunded"):
            continue
        if (o.get("paid_at") or o.get("created_at") or "") < since:
            continue
        src = o.get("source") or clients.get(o.get("chat_id"), ("unknown",))[0]
        r = row(src)
        r["paid"] += 1
        r["revenue"] += o["price_rub"]
    out = sorted(rows.values(), key=lambda r: (-r["revenue"], -r["starts"], r["source"]))
    total = {k: sum(r[k] for r in out) for k in ("starts", "previews", "paid", "revenue")}
    return out, total


def channels(rows):
    """Свёртка по каналу (префикс до «_»): ig, vk, yt, pin, tg, ad, vkads, p …"""
    agg = {}
    for r in rows:
        ch = r["source"].split("_")[0] if "_" in r["source"] else r["source"]
        a = agg.setdefault(ch, {"source": ch, "starts": 0, "previews": 0, "paid": 0, "revenue": 0})
        for k in ("starts", "previews", "paid", "revenue"):
            a[k] += r[k]
    return sorted(agg.values(), key=lambda r: (-r["revenue"], -r["starts"], r["source"]))


def line(r):
    return f"{r['source']}: старты {r['starts']} · превью {r['previews']} · оплаты {r['paid']} · {r['revenue']}₽"


def text(days):
    rows, total = report(days)
    head = f"📊 <b>Источники за {days} дн.</b>\nвсего: старты {total['starts']} · превью {total['previews']} · " \
           f"оплаты {total['paid']} · {total['revenue']}₽\n"
    if not rows:
        return head + "\nДанных пока нет."
    chans = "\n".join(B.esc(line(r)) for r in channels(rows))
    detail = "\n".join(B.esc(line(r)) for r in rows[:25])
    return f"{head}\n<b>По каналам</b>\n{chans}\n\n<b>По меткам</b>\n{detail}"


def cmd_sources(message):
    if not B.admin_only(message):
        return
    parts = (message.text or "").split()
    days_list = [int(parts[1])] if len(parts) > 1 and parts[1].isdigit() else [7, 30]
    for d in days_list:
        B.bot.send_message(message.chat.id, text(d)[:3900], parse_mode="HTML")


def register(bot_module):
    global B
    B = bot_module
    B.bot.message_handler(commands=["sources"])(cmd_sources)
