#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_scenes.py  ―  昭和レトロPOP スタイルのリール素材を生成（背景＋文字の2レイヤー）。

コンセプト「①第1木曜 興味喚起（入口）」:
  季節・世界観 / 空気感 / 「気になる」を作る（あえて売らない・保存/印象重視）

スタイル（昭和レトロPOP）:
  - クリーム地＋ハーフトーンのドット
  - 上＝赤帯／下＝紺帯、斜めのポラロイド写真
  - 極太ラウンド見出し（白文字＋紺フチ）で楽しくキャッチー
  - からし色のスタンプ・バッジ

出力:
  build/bg_XX.png : 背景（帯・ハーフトーン・ポラ写真・署名）… 不透明
  build/tx_XX.png : 文字（見出し・欧文・バッジ）… 透明PNG（アニメ用）
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

NS_B    = ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 0)
SERIF   = ("/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc", 0)
LAT_B   = ("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 0)
LAT     = ("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf", 0)

# ---- レトロPOP カラー ----
CREAM = (245, 233, 206)
DOT   = (233, 215, 176)
RED   = (202, 54, 47)
NAVY  = (33, 49, 82)
MUST  = (231, 176, 54)
WHITE = (252, 248, 240)

W, H = 1080, 1920
TOPBAND = 132
BOTBAND = 150

HEAD = "梅 田 名 物 さ ん ぽ"
SIGN = "おでん × スタンド  三徳六味 ／ 梅田 EST FOODHALL"

# (写真, 見出し, 欧文, バッジ語)  None は文字のみクロージング
SCENES = [
    ("IMG_0760修.jpg", "初夏の、さんぽ日和。",     "STROLL",  "初夏"),
    ("IMG_0724修.jpg", "おなじみ、あの赤。",        "UMEDA",   "名物"),
    ("IMG_0729修.jpg", "目印は、これ！",            "LANDMARK","目印"),
    ("IMG_0738修.jpg", "EST FOODHALL、とうちゃく。", "ARRIVED", "到着"),
    ("IMG_0769修.jpg", "電球サイン、ピカピカ。",     "LIGHTS",  "灯り"),
    ("IMG_0747修.jpg", "ちいさな、おでんスタンド。", "ODEN",    "発見"),
    ("IMG_0772修.jpg", "おでん、いっちょ。",         "STAND",   "湯気"),
    (None,            "梅田で、ひとやすみ。",       "PAUSE",   "また"),
]


def font(spec, size):
    return ImageFont.truetype(spec[0], size, index=spec[1])


def tw(d, s, f, tr=0):
    if not s:
        return 0
    return sum(f.getlength(c) for c in s) + tr * (len(s) - 1)


def tracked(d, x, y, s, f, fill, tr=0, stroke=0, sfill=None):
    cx = x
    for c in s:
        d.text((cx, y), c, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
        cx += f.getlength(c) + tr


def tracked_c(d, cx, y, s, f, fill, tr=0, stroke=0, sfill=None):
    tracked(d, cx - tw(d, s, f, tr) / 2, y, s, f, fill, tr, stroke, sfill)


def fit(d, s, spec, start, maxw, mn=46):
    sz = start
    while sz > mn:
        if tw(d, s, font(spec, sz), 2) <= maxw:
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


def halftone(d):
    step = 30
    for j, yy in enumerate(range(10, H, step)):
        for i, xx in enumerate(range(10, W, step)):
            r = 4 if (i + j) % 2 == 0 else 2
            d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=DOT)


def polaroid(photo, angle):
    pw, ph = 720, 812
    border, bottom = 26, 70
    fw, fh = pw + border * 2, ph + border + bottom
    card = Image.new("RGBA", (fw, fh), WHITE + (255,))
    ImageDraw.Draw(card).rectangle([0, 0, fw - 1, fh - 1], outline=NAVY, width=5)
    card.paste(cover(photo, pw, ph), (border, border))
    ImageDraw.Draw(card).rectangle(
        [border, border, border + pw - 1, border + ph - 1], outline=NAVY, width=4)
    # 影付きで回転
    sh = Image.new("RGBA", (fw + 60, fh + 60), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([30, 36, 30 + fw, 36 + fh], fill=(30, 22, 16, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(16))
    base = Image.new("RGBA", (fw + 60, fh + 60), (0, 0, 0, 0))
    base.alpha_composite(sh)
    base.alpha_composite(card, (30, 24))
    return base.rotate(angle, expand=True, resample=Image.BICUBIC)


def bands_sign(img):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, TOPBAND], fill=RED)
    d.rectangle([0, H - BOTBAND, W, H], fill=NAVY)
    tracked_c(d, W / 2, 40, HEAD, font(NS_B, 46), CREAM, tr=6)
    # 上帯のひし形アクセント（フォント非依存で描画）
    for sx in (110, W - 110):
        cy = TOPBAND / 2
        d.polygon([(sx, cy - 16), (sx + 14, cy), (sx, cy + 16), (sx - 14, cy)], fill=MUST)
    tracked_c(d, W / 2, H - BOTBAND + 52, SIGN, font(NS_B, 28), CREAM, tr=2)


def make_bg(i, photo):
    img = Image.new("RGBA", (W, H), CREAM + (255,))
    halftone(ImageDraw.Draw(img))
    if photo is not None:
        angle = 5 if i % 2 == 0 else -5
        pol = polaroid(photo, angle)
        img.alpha_composite(pol, (int(W / 2 - pol.width / 2), 250))
    bands_sign(img)
    img.convert("RGB").save(f"build/bg_{i:02d}.png")


def badge(layer, cx, cy, word):
    d = ImageDraw.Draw(layer)
    r = 96
    # スタンプ風：からし円＋紺の点線リング
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=MUST)
    import math
    for k in range(40):
        a = 2 * math.pi * k / 40
        x = cx + (r + 10) * math.cos(a)
        y = cy + (r + 10) * math.sin(a)
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=NAVY)
    f = fit(d, word, NS_B, 64, r * 1.6)
    w = tw(d, word, f)
    d.text((cx - w / 2, cy - f.size / 2 - 6), word, font=f, fill=NAVY)


def make_tx(i, photo, head, en, badge_word):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if photo is not None:
        # 見出し（白＋紺フチ・極太）
        hf = fit(d, head, NS_B, 86, W - 150)
        tracked_c(d, W / 2, 1280, head, hf, WHITE, tr=1, stroke=10, sfill=NAVY)
        # からしの下線
        uw = min(tw(d, head, hf, 1), W - 200)
        d.line([(W / 2 - uw / 2, 1410), (W / 2 + uw / 2, 1410)], fill=MUST, width=10)
        # 欧文
        tracked_c(d, W / 2, 1452, en, font(LAT_B, 40), NAVY, tr=14)
        # バッジ（右上）
        badge(img, W - 150, 360, badge_word)
    else:
        hf = fit(d, head, NS_B, 100, W - 150)
        tracked_c(d, W / 2, 820, head, hf, WHITE, tr=1, stroke=12, sfill=NAVY)
        uw = min(tw(d, head, hf, 1), W - 200)
        d.line([(W / 2 - uw / 2, 980), (W / 2 + uw / 2, 980)], fill=MUST, width=12)
        tracked_c(d, W / 2, 1030, "また、ふらっと。", font(NS_B, 46), NAVY, tr=4)
        badge(img, W / 2, 600, "梅田")
    img.save(f"build/tx_{i:02d}.png")


def main():
    os.makedirs("build", exist_ok=True)
    for i, (photo, head, en, bw) in enumerate(SCENES):
        make_bg(i, photo)
        make_tx(i, photo, head, en, bw)
        print(f"saved build/bg_{i:02d}.png  build/tx_{i:02d}.png")


if __name__ == "__main__":
    main()
