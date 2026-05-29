#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_cards.py

おでん×スタンド 三徳六味（ESTフードホール）の店舗情報カードを生成する。

  - output/endcard.png   : 動画末尾用の終了カード（1080x1920 / 9:16）
  - output/store_banner.png : フィード投稿用の店舗情報バナー（1080x1350 / 4:5）

位置づけは「①あえて売らない入口」のまま。
売り込みではなく "梅田駅すぐ・通し営業でふらっと通える" という
通いやすさ・世界観を、温かみのあるPOPなトーンで伝える。
"""

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"  # IPAGothic

# ---- カラーパレット（おでん/だしの温かみ + 梅田モニュメントの赤）----
BG     = (250, 246, 238)   # 生成りクリーム
INK    = (54, 41, 32)      # 焦げ茶（文字）
RED    = (210, 47, 47)     # アクセント赤
YELLOW = (242, 184, 42)    # 提灯/だしの黄
SUB    = (124, 112, 100)   # サブテキストのグレー
WHITE  = (255, 255, 255)


def font(size):
    return ImageFont.truetype(FONT_PATH, size)


def text_w(draw, s, f):
    b = draw.textbbox((0, 0), s, font=f)
    return b[2] - b[0]


def text_h(draw, s, f):
    b = draw.textbbox((0, 0), s, font=f)
    return b[3] - b[1]


def centered(draw, cx, y, s, f, fill, stroke=0, stroke_fill=None):
    w = text_w(draw, s, f)
    draw.text((cx - w / 2, y), s, font=f, fill=fill,
              stroke_width=stroke, stroke_fill=stroke_fill)


def pill(draw, cx, y, s, f, pad_x, pad_y, fill, txt_fill):
    """中央寄せの角丸ピル（チップ）を描く。戻り値は描画した高さ。"""
    w = text_w(draw, s, f)
    h = text_h(draw, s, f)
    box_w = w + pad_x * 2
    box_h = h + pad_y * 2
    x0 = cx - box_w / 2
    draw.rounded_rectangle([x0, y, x0 + box_w, y + box_h],
                           radius=box_h / 2, fill=fill)
    # テキストは bbox の上方オフセットを補正して中央へ
    b = draw.textbbox((0, 0), s, font=f)
    draw.text((cx - w / 2 - b[0], y + pad_y - b[1]), s, font=f, fill=txt_fill)
    return box_h


def dot_line(draw, cx, y, width, color):
    """点線風の飾り（だしの湯気/区切り）。"""
    n = 5
    gap = 22
    r = 5
    total = (n - 1) * gap
    x = cx - total / 2
    for _ in range(n):
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
        x += gap


def draw_point(draw, x, y, mark_color, text, f, ink):
    """◯ + テキストの「通いやすさ」ポイント行。"""
    r = 14
    cy = y + text_h(draw, text, f) / 2
    draw.ellipse([x, cy - r, x + r * 2, cy + r], outline=mark_color, width=5)
    draw.text((x + r * 2 + 22, y), text, font=f, fill=ink)


# 店舗情報
NAME1 = "おでん × スタンド"
NAME2 = "三徳六味"
PLACE = "EST FOODHALL ／ 梅田"
ADDR  = "大阪市北区角田町3-25 EST FOODHALL"
TEL   = "06-6743-4501"
HOURS = "11:00 – 23:00（L.O. フード22:00）"
HOLID = "不定休（施設に準ずる）"


def make_endcard():
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    cx = W / 2

    # 上下に細い赤帯のアクセント
    d.rectangle([0, 0, W, 14], fill=RED)
    d.rectangle([0, H - 14, W, H], fill=RED)

    # 上部：通いやすさを伝えるタグ
    y = 300
    pill(d, cx, y, "梅田駅から、ふらっと。", font(46), 46, 26, RED, WHITE)

    # 店名
    y = 470
    centered(d, cx, y, NAME1, font(58), INK)
    y += 92
    centered(d, cx, y, NAME2, font(132), INK, stroke=2, stroke_fill=INK)
    y += 188
    centered(d, cx, y, PLACE, font(40), SUB)

    # 区切り
    y += 96
    dot_line(d, cx, y, W, YELLOW)

    # 通いやすさポイント
    y += 80
    f_pt = font(46)
    left = 180
    for t in ["梅田駅から徒歩すぐ",
              "11:00〜23:00 通し営業",
              "ランチもふらっと ¥1,000〜"]:
        draw_point(d, left, y, RED, t, f_pt, INK)
        y += 96

    # 下部インフォブロック（控えめに）
    y = 1470
    f_lbl = font(34)
    f_val = font(38)
    rows = [("住所", ADDR), ("TEL", TEL), ("営業", HOURS), ("定休", HOLID)]
    for lbl, val in rows:
        d.text((180, y), lbl, font=f_lbl, fill=RED)
        d.text((300, y - 2), val, font=f_val, fill=INK)
        y += 60

    # フッターの一言（世界観）
    centered(d, cx, H - 90, "また、ふらっと。", font(40), SUB)

    img.save("output/endcard.png")
    print("saved output/endcard.png")


def make_banner():
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    cx = W / 2

    # 枠（角丸の内枠）
    d.rounded_rectangle([28, 28, W - 28, H - 28], radius=40, outline=RED, width=8)

    # タグ
    y = 96
    pill(d, cx, y, "梅田駅から、ふらっと。", font(40), 40, 22, RED, WHITE)

    # 店名
    y = 230
    centered(d, cx, y, NAME1, font(50), INK)
    y += 78
    centered(d, cx, y, NAME2, font(118), INK, stroke=2, stroke_fill=INK)
    y += 168
    centered(d, cx, y, PLACE, font(38), SUB)

    # 区切り
    y += 70
    dot_line(d, cx, y, W, YELLOW)

    # 情報テーブル
    y += 70
    f_lbl = font(36)
    f_val = font(40)
    rows = [("営業時間", "11:00 – 23:00"),
            ("",         "L.O. フード22:00／ドリンク22:15"),
            ("定休日",   "不定休（施設に準ずる）"),
            ("ランチ",   "平均 ¥1,000"),
            ("ディナー", "平均 ¥3,500"),
            ("TEL",      TEL),
            ("住所",     "大阪市北区角田町3-25"),
            ("",         "EST FOODHALL")]
    for lbl, val in rows:
        if lbl:
            d.text((110, y), lbl, font=f_lbl, fill=RED)
        d.text((360, y - 2), val, font=f_val, fill=INK)
        y += 62

    img.save("output/store_banner.png")
    print("saved output/store_banner.png")


if __name__ == "__main__":
    import os
    os.makedirs("output", exist_ok=True)
    make_endcard()
    make_banner()
