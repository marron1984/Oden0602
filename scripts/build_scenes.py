#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_scenes.py  ―  写真フルブリード（全画面）主役のシネマティック構成。

コンセプト「①第1木曜 興味喚起（入口）」:
  季節・世界観 / 空気感 / 「気になる」を作る（あえて売らない・保存/印象重視）

構図:
  - 写真を画面いっぱい（1080x1920）に使い、軽くグレーディング
  - 下部に黒のグラデーション（スクリム）で文字を読みやすく
  - 文字は最小限：小さな欧文キッカー＋細い金罫＋短い和文一行
  - 没入感を主役に、文字は控えめ

出力:
  build/bg_XX.png : 全画面写真＋グレーディング＋下スクリム … 不透明
  build/tx_XX.png : 上ラベル＋下キャプション … 透明PNG（アニメ用）
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

NS_B  = ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 0)
NS_M  = ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 0)
LAT   = ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 0)

INK_W  = (250, 248, 244)
GOLD   = (212, 184, 120)
SOFT   = (228, 224, 216)

W, H = 1080, 1920

HEAD_L = "UMEDA, OSAKA"
HEAD_R = "EST FOODHALL"

# (写真, 欧文キッカー, 和文, クロージング?)
SCENES = [
    ("IMG_0760修.jpg", "SUMMER",    "初夏の、寄り道。",            False),
    ("IMG_0724修.jpg", "LANDMARK",  "梅田の、目印。",              False),
    ("IMG_0729修.jpg", "THE RED",   "あの赤に、会いに。",          False),
    ("IMG_0738修.jpg", "ARRIVE",    "お目当ては、この中に。",      False),
    ("IMG_0769修.jpg", "LIGHTS",    "灯りに、誘われて。",          False),
    ("IMG_0747修.jpg", "THE STAND", "ふらりと、おでんスタンド。",  False),
    ("IMG_0772修.jpg", "INSIDE",    "湯気の、向こうへ。",          True),
]


def font(spec, size):
    return ImageFont.truetype(spec[0], size, index=spec[1])


def tw(d, s, f, tr=0):
    if not s:
        return 0
    return sum(f.getlength(c) for c in s) + tr * (len(s) - 1)


def tracked(d, x, y, s, f, fill, tr=0):
    cx = x
    for c in s:
        d.text((cx, y), c, font=f, fill=fill)
        cx += f.getlength(c) + tr


def fit(d, s, spec, start, maxw, mn=46):
    sz = start
    while sz > mn:
        if tw(d, s, font(spec, sz), 1) <= maxw:
            return font(spec, sz)
        sz -= 2
    return font(spec, mn)


def cover(path, w, h):
    im = Image.open(path).convert("RGB")
    sr, dr = im.width / im.height, w / h
    if sr > dr:
        nh, nw = h, int(h * sr)
    else:
        nw, nh = w, int(w / sr)
    im = im.resize((nw, nh), Image.LANCZOS)
    l, t = (nw - w) // 2, (nh - h) // 2
    return im.crop((l, t, l + w, t + h))


def grade(im):
    im = ImageEnhance.Contrast(im).enhance(1.06)
    im = ImageEnhance.Color(im).enhance(1.10)
    im = ImageEnhance.Brightness(im).enhance(0.99)
    # ほんのり暖色
    warm = Image.new("RGB", im.size, (255, 226, 188))
    im = Image.blend(im, warm, 0.05)
    return im


def make_bg(i, photo):
    im = grade(cover(photo, W, H)).convert("RGBA")

    # 周辺減光（ビネット）
    v = Image.new("L", (W, H), 0)
    ImageDraw.Draw(v).ellipse([-W * 0.30, -H * 0.20, W * 1.30, H * 1.20], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(200))
    im.paste(Image.new("RGBA", (W, H), (0, 0, 0, 90)), (0, 0),
             Image.eval(v, lambda p: 255 - p))

    # 下スクリム（透明→黒）と 上の軽いスクリム
    grad = Image.new("L", (1, H), 0)
    for y in range(H):
        if y > H * 0.52:
            grad.putpixel((0, y), int(225 * ((y - H * 0.52) / (H * 0.48)) ** 1.3))
        elif y < H * 0.12:
            grad.putpixel((0, y), int(90 * (1 - y / (H * 0.12))))
    im.paste(Image.new("RGBA", (W, H), (8, 8, 12, 255)), (0, 0), grad.resize((W, H)))

    im.convert("RGB").save(f"build/bg_{i:02d}.png")


def make_tx(i, kicker, jp, closing):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 上：左右の小ラベル
    fl = font(LAT, 28)
    tracked(d, 84, 70, HEAD_L, fl, SOFT + (210,), tr=6)
    tracked(d, W - 84 - tw(d, HEAD_R, fl, 6), 70, HEAD_R, fl, SOFT + (210,), tr=6)

    # 下：キャプション（左寄せ）
    x = 84
    ky = 1486
    idx = f"N° {i + 1:02d}"
    label = f"{idx}    {kicker}"
    tracked(d, x, ky, label, font(LAT, 32), GOLD + (255,), tr=6)
    d.line([(x, ky + 52), (x + 76, ky + 52)], fill=GOLD + (255,), width=3)

    jf = fit(d, jp, NS_B, 78, W - 168)
    # 影 → 本文
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    tracked(ImageDraw.Draw(sh), x + 3, ky + 95, jp, jf, (0, 0, 0, 170), tr=1)
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(img)
    tracked(d, x, ky + 92, jp, jf, INK_W + (255,), tr=1)

    if closing:
        tracked(d, x, ky + 200, "また、ふらっと。", font(NS_M, 40), SOFT + (235,), tr=2)

    img.save(f"build/tx_{i:02d}.png")


def main():
    os.makedirs("build", exist_ok=True)
    for i, (photo, kicker, jp, closing) in enumerate(SCENES):
        make_bg(i, photo)
        make_tx(i, kicker, jp, closing)
        print(f"saved build/bg_{i:02d}.png  build/tx_{i:02d}.png")


if __name__ == "__main__":
    main()
