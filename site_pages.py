"""Сайт «Письма Алисы» на том же Flask, что и бот: главная, SEO-страницы поводов, День отца,
sitemap.xml, robots.txt, открытки-картинки. Кнопки ведут в бот с меткой w_<повод> (источник «web»).
Счётчик просмотров страниц — data/site_views.json (виден в /stats)."""
import html
import json
import os
import threading
from datetime import datetime

from flask import Response, abort, request, send_file

import occasions as OCC
from site_content import FATHER_DAY, PAGES

BOT = os.getenv("BOT_USERNAME", "alisanevskaya_letters_bot")
SITE_URL = os.getenv("SITE_URL", "https://alisabot-w-sergeyrubakha1s.mia0.amvera.tech").rstrip("/")
VERIFY_META = os.getenv("SITE_VERIFY_META", "")  # готовые <meta> подтверждения Яндекс/Google
HERE = os.path.dirname(os.path.abspath(__file__))
CARDS = os.path.join(HERE, "assets", "postcards")
_views_lock = threading.Lock()

CSS = """
:root{--paper:#f6efe3;--ink:#2b2420;--muted:#7a6d62;--accent:#a3322b;--card:#fffaf2;--line:#e4d8c6}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:18px/1.6 'Jost',system-ui,sans-serif}
a{color:var(--accent)}.wrap{max-width:860px;margin:0 auto;padding:0 18px}
header{padding:18px 0;border-bottom:1px solid var(--line)}header .wrap{display:flex;justify-content:space-between;align-items:center}
.logo{font-family:'Cormorant Garamond',serif;font-size:26px;font-weight:600;color:var(--ink);text-decoration:none}
h1{font-family:'Cormorant Garamond',serif;font-size:42px;line-height:1.15;margin:34px 0 14px}
h2{font-family:'Cormorant Garamond',serif;font-size:30px;margin:38px 0 10px}
.lead{font-size:20px;color:var(--muted)}
.btn{display:inline-block;background:var(--accent);color:#fff;padding:14px 26px;border-radius:40px;text-decoration:none;font-weight:600;margin:8px 8px 8px 0}
.btn.ghost{background:transparent;color:var(--accent);border:2px solid var(--accent)}
.hand{font-family:'Caveat',cursive;font-size:27px;line-height:1.35;background:var(--card);border-left:4px solid var(--accent);padding:12px 18px;margin:12px 0;border-radius:6px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:16px;overflow:hidden;text-decoration:none;color:var(--ink)}
.tile img{width:100%;aspect-ratio:4/5;object-fit:cover;display:block}.tile div{padding:12px 14px}.tile b{display:block}
.price{color:var(--accent);font-weight:600}.steps{counter-reset:s;list-style:none;padding:0}
.steps li{counter-increment:s;margin:10px 0;padding-left:44px;position:relative}
.steps li:before{content:counter(s);position:absolute;left:0;top:0;width:32px;height:32px;border-radius:50%;background:var(--accent);color:#fff;text-align:center;line-height:32px;font-weight:600}
.cta{background:var(--card);border:1px solid var(--line);border-radius:20px;padding:24px;margin:34px 0;text-align:center}
.hero-card{max-width:340px;width:100%;border-radius:14px;box-shadow:0 10px 30px rgba(60,40,20,.15);float:right;margin:0 0 16px 22px}
details{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin:10px 0}summary{font-weight:600;cursor:pointer}
footer{border-top:1px solid var(--line);margin-top:50px;padding:26px 0;color:var(--muted);font-size:15px}
@media(max-width:640px){h1{font-size:32px}.hero-card{float:none;margin:10px auto;display:block}}
"""


def bot_link(key):
    return f"https://t.me/{BOT}?start=w_{key}"


VIEWS_FILE = None  # задаётся в register()


def count_view(path):
    if not VIEWS_FILE or "bot" in request.headers.get("User-Agent", "").lower():
        return
    day = datetime.now().strftime("%Y-%m-%d")
    with _views_lock:
        try:
            with open(VIEWS_FILE, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        data.setdefault(day, {})
        data[day][path] = data[day].get(path, 0) + 1
        try:
            os.makedirs(os.path.dirname(VIEWS_FILE), exist_ok=True)
            with open(VIEWS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except OSError:
            pass  # счётчик не должен ронять страницу


def page(title, desc, body, path, faq=None):
    canonical = SITE_URL + path
    ld = ""
    if faq:
        ld = json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]},
            ensure_ascii=False)
        ld = f'<script type="application/ld+json">{ld}</script>'
    count_view(path)
    return f"""<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canonical}">{VERIFY_META}
<meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}">
<meta property="og:type" content="website"><meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE_URL}/card/family.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@500&family=Cormorant+Garamond:wght@600&family=Jost:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}</style>{ld}</head><body>
<header><div class="wrap"><a class="logo" href="/">Письма Алисы</a><a href="https://t.me/{BOT}?start=w_home">Открыть в Telegram</a></div></header>
<main class="wrap">{body}</main>
<footer><div class="wrap">Алиса Невская — цифровая героиня проекта «Когда трудно сказать важное — здесь находятся слова». Письма собирает ИИ по вашим ответам; оплата через ЮKassa.<br>
<a href="https://t.me/alisanevskaya_diary">Дневник в Telegram</a> · <a href="https://vk.ru/alisanevskaya_diary">ВКонтакте</a> · <a href="https://www.instagram.com/nevskaya.diary/">Instagram</a></div></footer>
</body></html>"""


def tiles():
    out = []
    for key in OCC.CATALOG_ORDER:
        p, meta = OCC.PRODUCTS[key], PAGES.get(key)
        if not meta:
            continue
        out.append(f'<a class="tile" href="/pismo/{meta["slug"]}"><img src="/card/{key}.jpg" alt="Открытка: {html.escape(p["title"])}" loading="lazy">'
                   f'<div><b>{p["icon"]} {html.escape(p["title"])}</b><span class="price">{p["price"]} ₽</span></div></a>')
    return '<div class="grid">' + "".join(out) + "</div>"


HOW = ('<h2>Как это работает</h2><ol class="steps"><li>Выбираете повод и отвечаете на 3–4 простых вопроса: кому, что вас связывает, какая деталь важна.</li>'
       '<li>Алиса собирает письмо вашими словами и открытку с ним — превью видно <b>до оплаты</b>.</li>'
       '<li>Отправляете близкому ссылку-конверт и получаете уведомление, когда он его откроет.</li></ol>')


def home():
    body = (f'<h1>Письмо и открытка к любому поводу — за 3 минуты</h1>'
            f'<p class="lead">Когда трудно сказать важное — Алиса помогает найти слова: маме и папе, любимым, другу, «прости» и «спасибо». От {OCC.price_from()} ₽.</p>'
            f'<a class="btn" href="https://t.me/{BOT}?start=w_home">Собрать письмо в Telegram</a>'
            f'<a class="btn ghost" href="https://t.me/{BOT}?start=pdf">50 фраз для трудных разговоров — бесплатно</a>'
            f'{HOW}<h2>Поводы</h2>{tiles()}'
            f'<div class="cta"><b>18 октября — День отца.</b><br><a href="/den-otca">Что написать папе →</a></div>')
    return page("Письмо с открыткой к любому поводу за 3 минуты — Письма Алисы",
                "Личное письмо и открытка маме, папе, любимым, другу: ответьте на 3 вопроса — Алиса соберёт слова. От 199 ₽, превью до оплаты.",
                body, "/")


def occasion(slug):
    key = next((k for k, v in PAGES.items() if v["slug"] == slug), None)
    if not key:
        abort(404)
    m, p = PAGES[key], OCC.PRODUCTS[key]
    tips = "".join(f"<li>{html.escape(t)}</li>" for t in m["tips"])
    ex = "".join(f'<div class="hand">{html.escape(e)}</div>' for e in m["examples"])
    faq = "".join(f"<details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>" for q, a in m["faq"])
    others = " · ".join(f'<a href="/pismo/{v["slug"]}">{html.escape(OCC.PRODUCTS[k]["title"])}</a>'
                        for k, v in PAGES.items() if k != key)
    body = (f'<img class="hero-card" src="/card/{key}.jpg" alt="Открытка «{html.escape(p["title"])}»">'
            f'<h1>{html.escape(m["h1"])}</h1><p class="lead">{html.escape(m["intro"])}</p>'
            f'<a class="btn" href="{bot_link(key)}">Собрать письмо с открыткой — {p["price"]} ₽</a>'
            f'<h2>Как написать</h2><ul>{tips}</ul><h2>Примеры фраз</h2>{ex}{HOW}'
            f'<div class="cta"><b>Не хочется подбирать слова самому?</b><p>Ответьте на 3 вопроса — Алиса соберёт письмо вашими деталями и открытку. Превью до оплаты.</p>'
            f'<a class="btn" href="{bot_link(key)}">Начать в Telegram</a></div>'
            f'<h2>Вопросы</h2>{faq}<h2>Другие поводы</h2><p>{others}</p>')
    return page(m["title"], m["desc"], body, f"/pismo/{slug}", m["faq"])


def father_day():
    fam = PAGES["family"]
    ex = "".join(f'<div class="hand">{html.escape(e)}</div>' for e in fam["examples"])
    body = (f'<img class="hero-card" src="/card/family.jpg" alt="Открытка папе на День отца">'
            f'<h1>{FATHER_DAY["h1"]}</h1><p class="lead">Папы редко говорят, что им важно. Но почти каждый ждёт одного: '
            f'услышать, что его забота не прошла зря. Вот слова, с которых можно начать — даже если вы давно не разговаривали.</p>'
            f'<a class="btn" href="{bot_link("family")}">Письмо папе с открыткой — 199 ₽</a>'
            f'<h2>10 фраз для папы</h2>{ex}<h2>Как начать, если давно не общались</h2><ul>'
            + "".join(f"<li>{html.escape(t)}</li>" for t in fam["tips"]) +
            f'</ul>{HOW}<div class="cta"><b>Успейте к 18 октября</b><p>Письмо готово за 3 минуты, ссылку-конверт можно отправить в любой мессенджер.</p>'
            f'<a class="btn" href="{bot_link("family")}">Собрать письмо папе</a></div>')
    return page(FATHER_DAY["title"], FATHER_DAY["desc"], body, "/den-otca", fam["faq"])


def sitemap():
    urls = ["/", "/den-otca"] + [f"/pismo/{v['slug']}" for v in PAGES.values()]
    day = datetime.now().strftime("%Y-%m-%d")
    xml = ('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           + "".join(f"<url><loc>{SITE_URL}{u}</loc><lastmod>{day}</lastmod></url>" for u in urls) + "</urlset>")
    return Response(xml, mimetype="application/xml")


def robots():
    return Response(f"User-agent: *\nDisallow: /stats/\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", mimetype="text/plain")


def card(key):
    path = os.path.join(CARDS, f"{os.path.basename(key)}.jpg")
    if not os.path.exists(path):
        abort(404)
    return send_file(path, mimetype="image/jpeg", max_age=86400)


# коды подтверждения прав (не секреты): Яндекс Вебмастер — файл yandex_<код>.html
YANDEX_CODES = {"0c8acc3e8bcc9a6a"}
GOOGLE_FILES = set()  # google<код>.html, если подтверждать Search Console файлом


def verify_yandex(code):
    if code not in YANDEX_CODES:
        abort(404)
    return ('<html>\n<head>\n<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">\n</head>\n'
            f'<body>Verification: {code}</body>\n</html>')


def verify_google(code):
    if code not in GOOGLE_FILES:
        abort(404)
    return f"google-site-verification: google{code}.html"


def register(app, data_dir):
    global VIEWS_FILE
    VIEWS_FILE = os.path.join(data_dir, "site_views.json")
    app.add_url_rule("/", "site_home", home)
    app.add_url_rule("/pismo/<slug>", "site_occasion", occasion)
    app.add_url_rule("/den-otca", "site_father", father_day)
    app.add_url_rule("/sitemap.xml", "site_sitemap", sitemap)
    app.add_url_rule("/robots.txt", "site_robots", robots)
    app.add_url_rule("/card/<key>.jpg", "site_card", card)
    app.add_url_rule("/yandex_<code>.html", "site_verify_yandex", verify_yandex)
    app.add_url_rule("/google<code>.html", "site_verify_google", verify_google)
