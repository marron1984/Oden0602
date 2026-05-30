#!/usr/bin/env bash
#
# make_reel.sh ―  昭和レトロPOP のリールを生成。
#
# 動き:
#   - 背景：ゆるいズーム（Ken Burns）
#   - 文字＆バッジ：各シーン頭でスライドアップ＋フェードイン
#   - シーン切替：スライド/ワイプ系を交互に使ってリズミカルに
#   - 画面下：時間で伸びるからし色プログレスバー（紺地の上）
#
# 仕様: output/final.mp4 / 1080x1920 / 3秒+1秒トランジション / 30fps
#       H.264 (libx264) / yuv420p / 音声なし
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(cd "$SCRIPT_DIR/.." && pwd)"

W=1080; H=1920; FPS=30
DISPLAY=3; FADE=1
CLIP=$((DISPLAY + FADE)); FRAMES=$((CLIP * FPS))
INTRO=0.5; RISE=34
OUT="output/final.mp4"

# レトロにリズムを出すトランジション（順に使用）
TRANS=(slideleft slideup slideright wipeup slideleft slideup slideright)

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
  PREP+="[${bg}:v]scale=1350:2400,zoompan=z='min(zoom+0.00045,1.06)':d=${FRAMES}:"
  PREP+="x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=${W}x${H}:fps=${FPS},setsar=1[bg${i}];"
  PREP+="[${tx}:v]format=rgba,fps=${FPS},setsar=1,fade=t=in:st=0:d=${INTRO}:alpha=1[tx${i}];"
  PREP+="[bg${i}][tx${i}]overlay=x=0:y='${RISE}*(1-min(t/${INTRO}\,1))':format=auto,"
  PREP+="format=yuv420p,setsar=1[v${i}];"
done

CHAIN=""; PREV="[v0]"
for ((i=1; i<N; i++)); do
  OFF=$(( DISPLAY * i ))
  TR=${TRANS[$(((i-1) % ${#TRANS[@]}))]}
  LBL="[x${i}]"; [[ "$i" -eq $((N-1)) ]] && LBL="[xf]"
  CHAIN+="${PREV}[v${i}]xfade=transition=${TR}:duration=${FADE}:offset=${OFF}${LBL};"
  PREV="$LBL"
done

# プログレスバー（紺地の上にからし色が伸びる）
BAR="[xf]drawbox=x=0:y=${H}-12:w=iw:h=12:color=0x213152@1.0:t=fill,"
BAR+="drawbox=x=0:y=${H}-12:w='iw*min(t/${TOTAL}\,1)':h=12:color=0xE7B036@1.0:t=fill[outv]"

FILTER="${PREP}${CHAIN}${BAR}"

ffmpeg -y "${INPUTS[@]}" -filter_complex "$FILTER" -map "[outv]" \
  -r "$FPS" -c:v libx264 -pix_fmt yuv420p -profile:v high -preset veryfast -crf 18 \
  -movflags +faststart -an "$OUT"

echo "完成: $OUT"
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,pix_fmt,codec_name \
  -show_entries format=duration -of default=noprint_wrappers=1 "$OUT"
