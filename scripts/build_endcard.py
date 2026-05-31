#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_endcard.py ― 動画の最後に入れる QRエンドカードを生成（1080x1920）。"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

QR = "qr.png"            # 日本語名のUnicode正規化差異を避けASCIIコピーを使用
W, H = 1080, 1920
BG = (255, 255, 255)
INK = (33, 30, 27)
GOLD = (212, 184, 120)
GRAY = (120, 112, 101)
NS_B = ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 0)
LAT = ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 0)


def font(s, sz):
    return ImageFont.truetype(s[0], sz, index=s[1])


def tw(d, s, f, tr=0):
    return sum(f.getlength(c) for c in s) + tr * (len(s) - 1) if s else 0


def tracked_c(d, cx, y, s, f, fill, tr=0):
    x = cx - tw(d, s, f, tr) / 2
    for c in s:
        d.text((x, y), c, font=f, fill=fill)
        x += f.getlength(c) + tr


def main():
    os.makedirs("build", exist_ok=True)
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    tracked_c(d, W / 2, 168, "UMEDA, OSAKA", font(LAT, 30), GRAY, tr=6)
    tracked_c(d, W / 2, 226, "おでん × スタンド  三徳六味", font(NS_B, 44), INK, tr=2)
    d.line([(W / 2 - 60, 306), (W / 2 + 60, 306)], fill=GOLD, width=4)

    # QR（画像が文言入りのため大きく見せる・スキャンしやすく）
    qr = Image.open(QR).convert("RGB")
    target_w = 860
    qh = int(target_w * qr.height / qr.width)
    qr = qr.resize((target_w, qh), Image.LANCZOS)
    qx, qy = (W - target_w) // 2, 400
    pad = 30
    # 影
    base = img.convert("RGBA")
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        [qx - pad, qy - pad + 14, qx + target_w + pad, qy + qh + pad + 18],
        radius=36, fill=(30, 22, 16, 70))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(20)))
    img = base.convert("RGB")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([qx - pad, qy - pad, qx + target_w + pad, qy + qh + pad],
                        radius=36, outline=(232, 232, 232), width=2, fill=(255, 255, 255))
    img.paste(qr, (qx, qy))

    tracked_c(d, W / 2, H - 150, "また、ふらっと。", font(NS_B, 40), GRAY, tr=2)

    img.save("build/endcard.png")
    print("saved build/endcard.png")


if __name__ == "__main__":
    main()
