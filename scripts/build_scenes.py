#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_scenes.py

コンセプト「①第1木曜 興味喚起（入口）」に沿った、可愛く・POPなリール用シーン画像を生成する。

  テーマ : 季節・世界観 / 空気感・しつらえ
  役割   : 「気になる」を作る（あえて売らない・保存/印象重視）

各シーンは 1080x1920（9:16）で、
  - 生成りクリームの背景（淡いドット）
  - 角丸＋白フチ＋やわらかい影の写真フレーム
  - 手書き風の空気感コピー
  - 共通のシリーズ見出し／署名／ページドット
を備える。写真は厳選し、テンポよく "梅田さんぽ → おでんスタンド" の世界観を見せる。

出力: build/scene_00.png ... （make_reel.sh から使用）
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_PATH = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"  # IPAGothic

# ---- カラー（だしの温かみ × 梅田モニュメントの赤）----
BG       = (250, 245, 236)   # 生成りクリーム
DOT      = (244, 236, 222)   # 背景ドット（ごく薄く）
INK      = (58, 44, 35)      # 焦げ茶（メイン文字）
RED      = (213, 53, 49)     # アクセント赤
YELLOW   = (240, 186, 60)    # 提灯/だしの黄
SUB      = (150, 136, 122)   # サブグレー
WHITE    = (255, 255, 255)
SHADOW   = (60, 45, 35)

W, H = 1080, 1920

# シリーズ見出しと署名（売り込みではなく世界観の署名）
KICKER = "梅 田 、 ふ ら り"
SIGN   = "おでん × スタンド 三徳六味 ／ 梅田 EST FOODHALL"

# (写真ファイル, コピー) … None は文字のみのクロージング
SCENES = [
    ("IMG_0760修.jpg", "初夏の梅田、さんぽ日和。"),
    ("IMG_0724修.jpg", "おなじみの、あの赤。"),
    ("IMG_0729修.jpg", "これ、目印。"),
    ("IMG_0738修.jpg", "EST FOODHALL、ふらり。"),
    ("IMG_0769修.jpg", "電球サインに、誘われて。"),
    ("IMG_0747修.jpg", "ちいさな、おでんスタンド。"),
    ("IMG_0772修.jpg", "おでん × スタンド。湯気の向こう。"),
    (None,            "梅田で、ひとやすみ。"),   # クロージング（文字のみ）
]


def font(size):
    return ImageFont.truetype(FONT_PATH, size)


def tw(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0]


def th(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[3] - b[1]


def centered(d, cx, y, s, f, fill, stroke=0, stroke_fill=None):
    b = d.textbbox((0, 0), s, font=f)
    w = b[2] - b[0]
    d.text((cx - w / 2 - b[0], y - b[1]), s, font=f, fill=fill,
           stroke_width=stroke, stroke_fill=stroke_fill)


def draw_background(img, d):
    """クリーム地＋淡いドット模様。"""
    d.rectangle([0, 0, W, H], fill=BG)
    step = 64
    r = 3
    for yy in range(40, H, step):
        off = (step // 2) if (yy // step) % 2 else 0
        for xx in range(40 + off, W, step):
            d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=DOT)


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0], size[1]],
                                        radius=radius, fill=255)
    return m


def paste_photo(img, photo_path, box, radius=42, border=16):
    """box=(x0,y0,x1,y1) に、白フチ＋影付きの角丸写真を配置。"""
    x0, y0, x1, y1 = box
    pw, ph = x1 - x0, y1 - y0

    # --- 影 ---
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    pad = border
    sd.rounded_rectangle([x0 - pad, y0 - pad + 16, x1 + pad, y1 + pad + 22],
                         radius=radius + pad, fill=SHADOW + (90,))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    img.alpha_composite(shadow)

    # --- 白フチ ---
    wd = ImageDraw.Draw(img)
    wd.rounded_rectangle([x0 - border, y0 - border, x1 + border, y1 + border],
                         radius=radius + border, fill=WHITE + (255,))

    # --- 写真（4:5 を box にフィットさせて中央クロップ）---
    ph_img = Image.open(photo_path).convert("RGB")
    src_ratio = ph_img.width / ph_img.height
    dst_ratio = pw / ph
    if src_ratio > dst_ratio:
        nh = ph
        nw = int(nh * src_ratio)
    else:
        nw = pw
        nh = int(nw / src_ratio)
    ph_img = ph_img.resize((nw, nh), Image.LANCZOS)
    left = (nw - pw) // 2
    top = (nh - ph) // 2
    ph_img = ph_img.crop((left, top, left + pw, top + ph))

    mask = rounded_mask((pw, ph), radius)
    img.paste(ph_img, (x0, y0), mask)


def draw_header_footer(d, idx, total):
    cx = W / 2
    # 上：シリーズ見出し（小・字間あき）＋赤い細ライン
    centered(d, cx, 120, KICKER, font(38), RED)
    d.rounded_rectangle([cx - 70, 178, cx + 70, 184], radius=3, fill=YELLOW)

    # 下：ページドット
    n = total
    gap = 34
    rdot = 6
    total_w = (n - 1) * gap
    x = cx - total_w / 2
    yy = 1792
    for i in range(n):
        col = RED if i == idx else (220, 210, 198)
        d.ellipse([x - rdot, yy - rdot, x + rdot, yy + rdot], fill=col)
        x += gap
    # 下：署名（控えめ）
    centered(d, cx, 1838, SIGN, font(28), SUB)


def caption_block(d, lines, top_y):
    """写真下のコピー。半角スペースや句点で自然に1〜2行表示。"""
    cx = W / 2
    f = font(66)
    y = top_y
    for ln in lines:
        centered(d, cx, y, ln, f, INK)
        y += 92


def wrap_caption(text):
    # 「。」で区切って2行まで、長ければそのまま1行
    if "。" in text.rstrip("。"):
        parts = [p for p in text.split("。") if p]
        if len(parts) >= 2:
            return [parts[0] + "。", "。".join(parts[1:]) + "。"]
    return [text]


def make_photo_scene(idx, total, photo, caption):
    img = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    draw_background(img, d)

    # 写真フレーム（4:5）
    fw = 860
    fh = int(fw * 5 / 4)          # 1075
    x0 = (W - fw) // 2
    y0 = 250
    paste_photo(img, photo, (x0, y0, x0 + fw, y0 + fh))

    d = ImageDraw.Draw(img)
    caption_block(d, wrap_caption(caption), y0 + fh + 110)
    draw_header_footer(d, idx, total)
    return img.convert("RGB")


def make_closing_scene(idx, total, caption):
    img = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    draw_background(img, d)
    cx = W / 2

    # 中央に世界観コピー
    centered(d, cx, 760, "─  ─  ─", font(40), YELLOW)
    centered(d, cx, 850, caption, font(86), INK, stroke=1, stroke_fill=INK)
    centered(d, cx, 1010, "また、ふらっと。", font(48), SUB)
    centered(d, cx, 1140, "─  ─  ─", font(40), YELLOW)

    draw_header_footer(d, idx, total)
    return img.convert("RGB")


def main():
    os.makedirs("build", exist_ok=True)
    total = len(SCENES)
    for i, (photo, cap) in enumerate(SCENES):
        if photo is None:
            scene = make_closing_scene(i, total, cap)
        else:
            scene = make_photo_scene(i, total, photo, cap)
        out = f"build/scene_{i:02d}.png"
        scene.save(out)
        print("saved", out)


if __name__ == "__main__":
    main()
