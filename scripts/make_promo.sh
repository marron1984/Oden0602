#!/usr/bin/env bash
#
# make_promo.sh
# 「①あえて売らない入口」リール（output/final.mp4）の末尾に、
# 店舗情報の終了カード（output/endcard.png）を 1秒クロスフェードで付け足し、
# プロモーション版 output/promo.mp4 を書き出す。
#
# 位置づけは①のまま。終了カードは "梅田駅すぐ・通し営業でふらっと通える"
# という通いやすさ・世界観を控えめに伝えるもの。
#
# 仕様（本編と統一）:
#   1080x1920 / 30fps / H.264 (libx264) / yuv420p / 音声なし
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

W=1080
H=1920
FPS=30
FADE=1          # クロスフェード秒数
CARD_HOLD=5     # 終了カードの表示秒数（フェード含む）
BASE="output/final.mp4"
CARD="output/endcard.png"
OUT="output/promo.mp4"

# 終了カードが無ければ生成
if [[ ! -f "$CARD" ]]; then
  echo "endcard が無いので生成します..."
  python3 scripts/make_cards.py
fi

# 本編の長さを取得し、xfade の offset（= 本編尺 - フェード）を算出
BASE_DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$BASE")
OFFSET=$(awk -v d="$BASE_DUR" -v f="$FADE" 'BEGIN{printf "%.3f", d - f}')
echo "本編尺=${BASE_DUR}s / xfade offset=${OFFSET}s"

ffmpeg -y \
  -i "$BASE" \
  -loop 1 -t "$CARD_HOLD" -i "$CARD" \
  -filter_complex "\
[0:v]fps=${FPS},format=yuv420p,setsar=1[base];\
[1:v]scale=${W}:${H}:force_original_aspect_ratio=decrease,\
pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2:color=white,\
fps=${FPS},format=yuv420p,setsar=1[card];\
[base][card]xfade=transition=fade:duration=${FADE}:offset=${OFFSET}[outv]" \
  -map "[outv]" \
  -r "$FPS" \
  -c:v libx264 -pix_fmt yuv420p -profile:v high -preset medium -crf 20 \
  -movflags +faststart \
  -an \
  "$OUT"

echo "完成: $OUT"
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,pix_fmt,codec_name \
  -show_entries format=duration -of default=noprint_wrappers=1 "$OUT"
