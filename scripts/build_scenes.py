#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_scenes.py  ―  エディトリアル風リールの素材を「背景」と「文字」の2レイヤーで生成。

コンセプト「①第1木曜 興味喚起（入口）」:
  季節・世界観 / 空気感・しつらえ / 「気になる」を作る（あえて売らない・保存/印象重視）

ねらい（今回の強化）:
  - 文字を大きく・太く・くっきり（見やすさ／アピール感アップ）
  - 文字は別レイヤーにして、make_reel.sh 側でスライド＋フェード表示（動画っぽさ）

出力:
  build/bg_XX.png : 背景（ペーパー＋ヘッダー/フッター＋写真＋キーライン）… 不透明
  build/tx_XX.png : 文字（N°・罫・和文・欧文）… 透明PNG（アニメ用）
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---- フォント ----
JP_SERIF    = ("/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc", 0)
JP_SERIF_B  = ("/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc", 0)
JP_SANS_B   = ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 0)
LAT_SERIF   = ("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf", 0)
LAT_SERIF_I = ("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf", 0)

# ---- カラー ----
PAPER  = (244, 240, 233)
INK    = (33, 30, 27)
ACCENT = (176, 64, 48)    # 引き締めたテラコッタレッド（アピール）
GOLD   = (183, 156, 106)
GRAY   = (120, 112, 101)

W, H = 1080, 1920
M = 96

HEAD_L = "UMEDA, OSAKA"
HEAD_R = "EST FOODHALL"
SIGN_JP = "おでん × スタンド  三徳六味"
SIGN_EN = "SANTOKU ROKUMI"

# (写真, 和文, 欧文)  None は文字のみのクロージング
SCENES = [
    ("IMG_0760修.jpg", "初夏の、寄り道。",       "An early-summer detour."),
    ("IMG_0724修.jpg", "梅田、あの赤。",          "The landmark red."),
    ("IMG_0729修.jpg", "目印は、ここ。",          "Meet me right here."),
    ("IMG_0738修.jpg", "EST FOODHALL へ。",      "Step inside."),
    ("IMG_0769修.jpg", "灯りに、誘われて。",      "Drawn by the lights."),
    ("IMG_0747修.jpg", "ちいさな、立ち呑み。",    "A tiny oden stand."),
    ("IMG_0772修.jpg", "湯気の、向こうへ。",      "Beyond the steam."),
    (None,            "梅田で、ひとやすみ。",    "Take a pause in Umeda."),
]

CAP_TOP = 1408   # 写真下キャプションの基準Y


def font(spec, size):
    return ImageFont.truetype(spec[0], size, index=spec[1])


def tsize(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0], b[3] - b[1], b


def tracked_width(d, s, f, tr):
    if not s:
        return 0
    return sum(f.getlength(ch) for ch in s) + tr * (len(s) - 1)


def draw_tracked(d, x, y, s, f, fill, tr=0):
    cx = x
    for ch in s:
        d.text((cx, y), ch, font=f, fill=fill)
        cx += f.getlength(ch) + tr


def draw_tracked_center(d, cx, y, s, f, fill, tr=0):
    draw_tracked(d, cx - tracked_width(d, s, f, tr) / 2, y, s, f, fill, tr)


def centered(d, cx, y, s, f, fill):
    w, _, b = tsize(d, s, f)
    d.text((cx - w / 2 - b[0], y - b[1]), s, font=f, fill=fill)


def fit_font(d, s, spec, start, maxw, minsize=52):
    """maxw に収まる最大サイズの太字フォントを返す。"""
    size = start
    while size > minsize:
        f = font(spec, size)
        if tracked_width(d, s, f, 2) <= maxw:
            return f
        size -= 2
    return font(spec, minsize)


# ---------- 背景レイヤー ----------
def paper(img):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, H], fill=PAPER)
    v = Image.new("L", (W, H), 0)
    ImageDraw.Draw(v).ellipse([-W * 0.25, -H * 0.18, W * 1.25, H * 1.18], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(160))
    img.paste(Image.new("RGBA", (W, H), (18, 14, 10, 30)), (0, 0),
              Image.eval(v, lambda p: 255 - p))


def header_footer(d):
    ry = 158
    d.line([(M, ry), (W - M, ry)], fill=INK, width=2)
    fl = font(LAT_SERIF, 30)
    draw_tracked(d, M, ry - 44, HEAD_L, fl, INK, tr=6)
    wr = tracked_width(d, HEAD_R, fl, 6)
    draw_tracked(d, W - M - wr, ry - 44, HEAD_R, fl, INK, tr=6)

    fy = 1792
    d.line([(M, fy), (W - M, fy)], fill=INK, width=2)
    cx = W / 2
    draw_tracked_center(d, cx, fy + 26, SIGN_JP, font(JP_SERIF, 32), INK, tr=4)
    draw_tracked_center(d, cx, fy + 78, SIGN_EN, font(LAT_SERIF, 24), GRAY, tr=10)


def crop_to(path, pw, ph):
    im = Image.open(path).convert("RGB")
    sr, dr = im.width / im.height, pw / ph
    if sr > dr:
        nh, nw = ph, int(ph * sr)
    else:
        nw, nh = pw, int(pw / sr)
    im = im.resize((nw, nh), Image.LANCZOS)
    l, t = (nw - pw) // 2, (nh - ph) // 2
    return im.crop((l, t, l + pw, t + ph))


def make_bg(i, photo):
    img = Image.new("RGBA", (W, H), PAPER + (255,))
    paper(img)
    d = ImageDraw.Draw(img)
    if photo is not None:
        pw, ph = W - 2 * M, int((W - 2 * M) * 5 / 4)
        x0, y0 = M, 250
        x1, y1 = x0 + pw, y0 + ph
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rectangle([x0, y0 + 16, x1, y1 + 22], fill=(30, 22, 16, 80))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(26)))
        img.paste(crop_to(photo, pw, ph), (x0, y0))
        ImageDraw.Draw(img).rectangle([x0, y0, x1 - 1, y1 - 1], outline=INK, width=2)
    header_footer(ImageDraw.Draw(img))
    img.convert("RGB").save(f"build/bg_{i:02d}.png")


# ---------- 文字レイヤー（透明） ----------
def make_tx(i, photo, jp, en):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    idx = f"N° {i + 1:02d}"

    if photo is not None:
        x = M
        y = CAP_TOP
        # N°（アクセント）＋ゴールド罫
        draw_tracked(d, x, y, idx, font(LAT_SERIF, 36), ACCENT, tr=8)
        d.line([(x, y + 56), (x + 70, y + 56)], fill=GOLD, width=3)
        # 和文（太・大きく見やすく）
        jf = fit_font(d, jp, JP_SERIF_B, 92, W - 2 * M)
        draw_tracked(d, x, y + 96, jp, jf, INK, tr=2)
        # 欧文
        ef = font(LAT_SERIF_I, 40)
        _, _, b = tsize(d, en, ef)
        d.text((x - b[0], y + 232 - b[1]), en, font=ef, fill=GRAY)
    else:
        cx = W / 2
        draw_tracked_center(d, cx, 720, idx, font(LAT_SERIF, 38), ACCENT, tr=8)
        d.line([(cx - 44, 786), (cx + 44, 786)], fill=GOLD, width=3)
        jf = fit_font(d, jp, JP_SERIF_B, 104, W - 2 * M)
        centered(d, cx, 850, jp, jf, INK)
        centered(d, cx, 1018, en, font(LAT_SERIF_I, 44), GRAY)
        centered(d, cx, 1126, "また、ふらっと。", font(JP_SERIF, 42), GRAY)

    img.save(f"build/tx_{i:02d}.png")


def main():
    os.makedirs("build", exist_ok=True)
    for i, (photo, jp, en) in enumerate(SCENES):
        make_bg(i, photo)
        make_tx(i, photo, jp, en)
        print(f"saved build/bg_{i:02d}.png  build/tx_{i:02d}.png")


if __name__ == "__main__":
    main()
