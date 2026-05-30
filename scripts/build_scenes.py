#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_scenes.py  ―  エディトリアル（雑誌）風のおしゃれなリール用シーンを生成。

コンセプト「①第1木曜 興味喚起（入口）」:
  季節・世界観 / 空気感・しつらえ / 「気になる」を作る（あえて売らない・保存/印象重視）

デザイン言語（おしゃれ／editorial）:
  - 生成りペーパーの余白を活かしたミニマル構成
  - 明朝（Noto Serif CJK JP）の和文 ＋ セリフ体の欧文ミニキャプション
  - シャープな写真キーライン、N° のインデックス、細いゴールドの罫
  - くすんだテラコッタを唯一のアクセントに（梅田の赤への目配せ）

出力: build/scene_00.png …（make_reel.sh から使用）
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---- フォント ----
JP_SERIF      = ("/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc", 0)
JP_SERIF_B    = ("/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc", 0)
LAT_SERIF     = ("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf", 0)
LAT_SERIF_I   = ("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf", 0)

# ---- カラー（くすんだ上品なトーン）----
PAPER  = (244, 240, 233)
INK    = (38, 35, 31)
ACCENT = (166, 74, 58)    # くすんだテラコッタ
GOLD   = (183, 156, 106)  # 細い罫のゴールド
GRAY   = (138, 130, 118)
WHITE  = (255, 255, 255)

W, H = 1080, 1920
M = 96  # 左右マージン

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


def font(spec, size):
    path, idx = spec
    return ImageFont.truetype(path, size, index=idx)


def text_size(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0], b[3] - b[1], b


def tracked_width(d, s, f, tr):
    if not s:
        return 0
    return sum(f.getlength(ch) for ch in s) + tr * (len(s) - 1)


def draw_tracked(d, x, y, s, f, fill, tr=0):
    """字間 tr を空けて左から描く（ベースラインは共通／y は文字の上端）。"""
    cx = x
    for ch in s:
        d.text((cx, y), ch, font=f, fill=fill)
        cx += f.getlength(ch) + tr


def draw_tracked_center(d, cx, y, s, f, fill, tr=0):
    w = tracked_width(d, s, f, tr)
    draw_tracked(d, cx - w / 2, y, s, f, fill, tr)


def centered(d, cx, y, s, f, fill):
    w, _, b = text_size(d, s, f)
    d.text((cx - w / 2 - b[0], y - b[1]), s, font=f, fill=fill)


def paper(img, d):
    d.rectangle([0, 0, W, H], fill=PAPER)
    # ごく薄いビネット（四隅をわずかに沈める）
    v = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(v)
    vd.ellipse([-W * 0.25, -H * 0.18, W * 1.25, H * 1.18], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(160))
    dark = Image.new("RGBA", (W, H), (20, 16, 12, 26))
    inv = Image.eval(v, lambda p: 255 - p)
    img.paste(dark, (0, 0), inv)


def header_footer(d, idx, total):
    # 上：細い罫＋左右のラベル
    ry = 158
    d.line([(M, ry), (W - M, ry)], fill=INK, width=2)
    fl = font(LAT_SERIF, 30)
    draw_tracked(d, M, ry - 44, HEAD_L, fl, INK, tr=6)
    wr = tracked_width(d, HEAD_R, fl, 6)
    draw_tracked(d, W - M - wr, ry - 44, HEAD_R, fl, INK, tr=6)

    # 下：細い罫＋署名
    fy = 1792
    d.line([(M, fy), (W - M, fy)], fill=INK, width=2)
    cx = W / 2
    draw_tracked_center(d, cx, fy + 26, SIGN_JP, font(JP_SERIF, 32), INK, tr=4)
    draw_tracked_center(d, cx, fy + 78, SIGN_EN, font(LAT_SERIF, 24), GRAY, tr=10)


def index_label(n):
    return f"N° {n:02d}"


def caption_block(d, x, y, idx, jp, en):
    # N° インデックス（テラコッタ）＋ゴールドの短い罫
    draw_tracked(d, x, y, index_label(idx + 1), font(LAT_SERIF, 34), ACCENT, tr=8)
    d.line([(x, y + 54), (x + 64, y + 54)], fill=GOLD, width=2)
    # 和文（明朝）
    jf = font(JP_SERIF, 66)
    draw_tracked(d, x, y + 92, jp, jf, INK, tr=3)
    # 欧文（セリフ・イタリック）
    ef = font(LAT_SERIF_I, 36)
    _, _, b = text_size(d, en, ef)
    d.text((x - b[0], y + 196 - b[1]), en, font=ef, fill=GRAY)


def crop_to(photo_path, pw, ph):
    im = Image.open(photo_path).convert("RGB")
    sr = im.width / im.height
    dr = pw / ph
    if sr > dr:
        nh = ph; nw = int(nh * sr)
    else:
        nw = pw; nh = int(nw / sr)
    im = im.resize((nw, nh), Image.LANCZOS)
    l = (nw - pw) // 2; t = (nh - ph) // 2
    return im.crop((l, t, l + pw, t + ph))


def make_photo_scene(idx, total, photo, jp, en):
    img = Image.new("RGBA", (W, H), PAPER + (255,))
    d = ImageDraw.Draw(img)
    paper(img, d)
    d = ImageDraw.Draw(img)

    # 写真（4:5・シャープな角）
    pw = W - 2 * M           # 888
    ph = int(pw * 5 / 4)     # 1110
    x0, y0 = M, 250
    x1, y1 = x0 + pw, y0 + ph

    # やわらかい影
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([x0, y0 + 16, x1, y1 + 22], fill=(30, 22, 16, 70))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(24)))

    img.paste(crop_to(photo, pw, ph), (x0, y0))
    d = ImageDraw.Draw(img)
    d.rectangle([x0, y0, x1 - 1, y1 - 1], outline=INK, width=2)   # キーライン

    caption_block(d, M, y1 + 56, idx, jp, en)
    header_footer(d, idx, total)
    return img.convert("RGB")


def make_closing_scene(idx, total, jp, en):
    img = Image.new("RGBA", (W, H), PAPER + (255,))
    d = ImageDraw.Draw(img)
    paper(img, d)
    d = ImageDraw.Draw(img)
    cx = W / 2

    draw_tracked_center(d, cx, 760, index_label(idx + 1), font(LAT_SERIF, 34), ACCENT, tr=8)
    d.line([(cx - 40, 824), (cx + 40, 824)], fill=GOLD, width=2)
    centered(d, cx, 880, jp, font(JP_SERIF, 84), INK)
    centered(d, cx, 1030, en, font(LAT_SERIF_I, 40), GRAY)
    centered(d, cx, 1130, "また、ふらっと。", font(JP_SERIF, 40), GRAY)

    header_footer(d, idx, total)
    return img.convert("RGB")


def main():
    os.makedirs("build", exist_ok=True)
    total = len(SCENES)
    for i, (photo, jp, en) in enumerate(SCENES):
        if photo is None:
            scene = make_closing_scene(i, total, jp, en)
        else:
            scene = make_photo_scene(i, total, photo, jp, en)
        out = f"build/scene_{i:02d}.png"
        scene.save(out)
        print("saved", out)


if __name__ == "__main__":
    main()
