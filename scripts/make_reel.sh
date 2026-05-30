#!/usr/bin/env bash
#
# make_reel.sh ―  写真フルブリード主役のシネマティック・リールを生成。
#
# 動き:
#   - 背景写真：ゆるいズーム（Ken Burns）で没入感
#   - 文字：各シーン頭でやわらかくフェードイン＋わずかに上へ
#   - シーン切替：ディゾルブ（fade）で上品に
#   - 画面上部：時間で伸びる細い金のプログレスバー
#
# 仕様: output/final.mp4 / 1080x1920 / 3秒+1秒ディゾルブ / 30fps
#       H.264 (libx264) / yuv420p / 音声なし
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(cd "$SCRIPT_DIR/.." && pwd)"

W=1080; H=1920; FPS=30
DISPLAY=3; FADE=1
CLIP=$((DISPLAY + FADE)); FRAMES=$((CLIP * FPS))
INTRO=0.7; RISE=22
OUT="output/final.mp4"

if ! ls build/bg_*.png >/dev/null 2>&1; then python3 scripts/build_scenes.py; fi
mapfile -t BGS < <(ls -1 build/bg_*.png | sort)
N=${#BGS[@]}
TOTAL=$(( DISPLAY * (N - 1) + CLIP ))
echo "シーン数:${N}  全体尺:${TOTAL}s"
mkdir -p output

INPUTS=()
for ((i=0; i<N; i++)); do
  INPUTS+=(-i "build/bg_$(printf '%02d' "$i").png")
  INPUTS+=(-loop 1 -t "$CLIP" -i "build/tx_$(printf '%02d' "$i").png")
done

PREP=""
for ((i=0; i<N; i++)); do
  bg=$((i*2)); tx=$((i*2+1))
  # 背景：1.25倍→ゆるくズーム（方向を交互に：寄る/引く風の演出）
  if (( i % 2 == 0 )); then
    Z="z='min(zoom+0.00035,1.05)'"
  else
    Z="z='if(eq(on,0),1.05,max(1.0,zoom-0.00035))'"
  fi
  PREP+="[${bg}:v]scale=1350:2400,zoompan=${Z}:d=${FRAMES}:"
  PREP+="x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=${W}x${H}:fps=${FPS},setsar=1[bg${i}];"
  PREP+="[${tx}:v]format=rgba,fps=${FPS},setsar=1,fade=t=in:st=0:d=${INTRO}:alpha=1[tx${i}];"
  PREP+="[bg${i}][tx${i}]overlay=x=0:y='-${RISE}*(1-min(t/${INTRO}\,1))':format=auto,"
  PREP+="format=yuv420p,setsar=1[v${i}];"
done

CHAIN=""; PREV="[v0]"
for ((i=1; i<N; i++)); do
  OFF=$(( DISPLAY * i ))
  LBL="[x${i}]"; [[ "$i" -eq $((N-1)) ]] && LBL="[xf]"
  CHAIN+="${PREV}[v${i}]xfade=transition=fade:duration=${FADE}:offset=${OFF}${LBL};"
  PREV="$LBL"
done

# プログレスバー（上部・細い金）
BAR="[xf]drawbox=x=0:y=0:w=iw:h=5:color=white@0.28:t=fill,"
BAR+="drawbox=x=0:y=0:w='iw*min(t/${TOTAL}\,1)':h=5:color=0xD4B878@1.0:t=fill[outv]"

FILTER="${PREP}${CHAIN}${BAR}"

ffmpeg -y "${INPUTS[@]}" -filter_complex "$FILTER" -map "[outv]" \
  -r "$FPS" -c:v libx264 -pix_fmt yuv420p -profile:v high -preset veryfast -crf 18 \
  -movflags +faststart -an "$OUT"

echo "完成: $OUT"
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,pix_fmt,codec_name \
  -show_entries format=duration -of default=noprint_wrappers=1 "$OUT"
