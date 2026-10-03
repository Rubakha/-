"""Открытка к письму: фото-фон сверху, «бумага» снизу, заголовок с именем,
рукописная строка и подпись. PIL, без внешних сервисов.

render(product_key, title, line, sign, preview=False) -> bytes (JPEG 1080×1350)
"""
import io
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(BASE, "assets", "fonts")
BGS = os.path.join(BASE, "assets", "postcards")

W, H = 1080, 1350
PHOTO_H = 800
PAPER = (247, 241, 231)
INK = (52, 42, 34)
INK_SOFT = (96, 74, 58)
ACCENT = (150, 58, 52)  # сургучно-красный


def _font(name, size, variation=None):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    if variation:
        try:
            f.set_variation_by_name(variation)
        except Exception:
            pass
    return f


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _fit(draw, text, fname, variation, start, minimum, max_w, max_lines):
    size = start
    while size >= minimum:
        f = _font(fname, size, variation)
        lines = _wrap(draw, text, f, max_w)
        if len(lines) <= max_lines:
            return f, lines
        size -= 2
    f = _font(fname, minimum, variation)
    return f, _wrap(draw, text, f, max_w)[:max_lines]


def _background(product_key):
    path = os.path.join(BGS, f"{product_key}.jpg")
    if not os.path.exists(path):
        return Image.new("RGB", (W, PHOTO_H), (200, 180, 160))
    im = Image.open(path).convert("RGB")
    scale = max(W / im.width, PHOTO_H / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    x = (im.width - W) // 2
    y = (im.height - PHOTO_H) // 2
    return im.crop((x, y, x + W, y + PHOTO_H))


def _paper_texture():
    rnd = random.Random(7)
    paper = Image.new("RGB", (W, H), PAPER)
    noise = Image.effect_noise((W, H), 18).convert("L").filter(ImageFilter.GaussianBlur(0.6))
    paper = Image.blend(paper, Image.merge("RGB", (noise,) * 3), 0.035)
    d = ImageDraw.Draw(paper)
    for _ in range(40):  # редкие волокна бумаги
        x, y = rnd.randint(0, W), rnd.randint(PHOTO_H, H)
        d.line([(x, y), (x + rnd.randint(-30, 30), y + rnd.randint(-4, 4))], fill=(232, 224, 212), width=1)
    return paper


def render(product_key, title, line, sign, preview=False):
    card = _paper_texture()
    photo = _background(product_key)
    # фото плавно переходит в бумагу
    mask = Image.new("L", (W, PHOTO_H), 255)
    md = ImageDraw.Draw(mask)
    fade = 110
    for i in range(fade):
        md.line([(0, PHOTO_H - fade + i), (W, PHOTO_H - fade + i)], fill=int(255 * (1 - i / fade) ** 1.6))
    card.paste(photo, (0, 0), mask)

    d = ImageDraw.Draw(card)
    margin = 110
    max_w = W - 2 * margin

    # сургучная печать на стыке
    cx, cy, r = W // 2, PHOTO_H - 40, 38
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ACCENT)
    d.ellipse([cx - r + 7, cy - r + 7, cx + r - 7, cy + r - 7], outline=(185, 96, 88), width=2)
    seal_f = _font("CormorantGaramond.ttf", 44, "Bold")
    d.text((cx, cy - 2), "А", font=seal_f, fill=(245, 225, 210), anchor="mm")

    y = PHOTO_H + 30
    t_font, t_lines = _fit(d, title, "CormorantGaramond.ttf", "SemiBold", 70, 46, max_w, 2)
    for ln in t_lines:
        d.text((W // 2, y), ln, font=t_font, fill=INK, anchor="ma")
        y += int(t_font.size * 1.12)

    y += 16
    l_font, l_lines = _fit(d, line, "Caveat.ttf", "Regular", 58, 40, max_w, 3)
    for ln in l_lines:
        d.text((W // 2, y), ln, font=l_font, fill=INK_SOFT, anchor="ma")
        y += int(l_font.size * 1.18)

    if sign:
        s_font = _font("Caveat.ttf", 46, "Bold")
        sy = max(y + 18, H - 175)
        d.text((W - margin, sy), f"— {sign}", font=s_font, fill=INK, anchor="ra")

    foot = _font("Jost-Medium.ttf", 21)
    label = "ПИСЬМО ОТ АЛИСЫ НЕВСКОЙ"
    spaced = " ".join(label)
    d.text((W // 2, H - 62), spaced, font=foot, fill=(170, 150, 132), anchor="ma")

    if preview:
        layer = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        wf = _font("Jost-Medium.ttf", 54)
        for yy in range(0, H * 2, 230):
            ld.text((0, yy), ("превью   " * 12), font=wf, fill=(255, 255, 255, 115))
        layer = layer.rotate(28, resample=Image.BICUBIC)
        layer = layer.crop((W // 2, H // 2, W // 2 + W, H // 2 + H))
        card = card.convert("RGBA")
        card.alpha_composite(layer)
        card = card.convert("RGB")

    buf = io.BytesIO()
    card.save(buf, "JPEG", quality=90)
    return buf.getvalue()
