#!/usr/bin/env bash
#
# make_reel.sh
# コンセプト「①第1木曜 興味喚起（入口）」のリールを生成する。
#   - build/scene_*.png（build_scenes.py で生成）を素材に
#   - 各シーンへ ゆるいズーム（Ken Burns）で動きを付け
#   - 1秒クロスフェードで繋ぎ、保存・印象重視のテンポに仕上げる
#
# 仕様:
#   出力       : output/final.mp4
#   解像度     : 1080x1920（縦型 9:16）
#   1枚の表示  : 3秒（+ クロスフェード1秒）
#   フレーム   : 30fps
#   コーデック : H.264 (libx264) / yuv420p（インスタ互換）
#   音声       : なし
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

W=1080
H=1920
FPS=30
DISPLAY=3        # 表示秒
FADE=1           # クロスフェード秒
CLIP=$((DISPLAY + FADE))      # 1シーンの長さ=4秒
FRAMES=$((CLIP * FPS))        # 120フレーム
OUT="output/final.mp4"

# シーン画像が無ければ生成
if ! ls build/scene_*.png >/dev/null 2>&1; then
  python3 scripts/build_scenes.py
fi
mapfile -t SCENES < <(ls -1 build/scene_*.png | sort)
N=${#SCENES[@]}
echo "シーン数: ${N}"

mkdir -p output

# ---- 入力とフィルタを構築 ----
# zoompan は「1枚の静止画から d フレームを生成」するため、入力はループさせない。
# （-loop でフレームを与えると d と掛け算になり極端に重くなる）
INPUTS=()
PREP=""
for i in "${!SCENES[@]}"; do
  INPUTS+=(-i "${SCENES[$i]}")
  # 1.25倍に拡大して余白を確保 → ゆるく寄るズーム（中央基準）→ 1080x1920 / 30fps へ
  PREP+="[${i}:v]scale=1350:2400,"
  PREP+="zoompan=z='min(zoom+0.00035,1.045)':d=${FRAMES}:"
  PREP+="x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=${W}x${H}:fps=${FPS},"
  PREP+="setsar=1,format=yuv420p[v${i}];"
done

# xfade チェーン
CHAIN=""
PREV="[v0]"
for ((i=1; i<N; i++)); do
  OFFSET=$(( DISPLAY * i ))
  if [[ "$i" -eq $((N-1)) ]]; then LABEL="[outv]"; else LABEL="[x${i}]"; fi
  CHAIN+="${PREV}[v${i}]xfade=transition=fade:duration=${FADE}:offset=${OFFSET}${LABEL};"
  PREV="${LABEL}"
done

FILTER="${PREP}${CHAIN}"
FILTER="${FILTER%;}"

ffmpeg -y "${INPUTS[@]}" \
  -filter_complex "$FILTER" \
  -map "[outv]" \
  -r "$FPS" \
  -c:v libx264 -pix_fmt yuv420p -profile:v high -preset veryfast -crf 19 \
  -movflags +faststart \
  -an \
  "$OUT"

echo "完成: $OUT"
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,pix_fmt,codec_name \
  -show_entries format=duration -of default=noprint_wrappers=1 "$OUT"
