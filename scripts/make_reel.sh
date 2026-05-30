#!/usr/bin/env bash
#
# make_reel.sh ―  コンセプト「①興味喚起（入口）」のおしゃれリールを生成。
#
# 動画らしさの強化:
#   - 背景写真：ゆるいズーム（Ken Burns）
#   - 文字レイヤー：各シーンの頭でスライドアップ＋フェードイン（モーション）
#   - 画面下：時間で伸びる細いプログレスバー
#
# 仕様:
#   出力 output/final.mp4 / 1080x1920 / 1枚3秒+1秒クロスフェード / 30fps
#   H.264 (libx264) / yuv420p / 音声なし
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(cd "$SCRIPT_DIR/.." && pwd)"

W=1080; H=1920; FPS=30
DISPLAY=3; FADE=1
CLIP=$((DISPLAY + FADE)); FRAMES=$((CLIP * FPS))
INTRO=0.6          # 文字の出現にかける秒数
RISE=30            # 文字の立ち上がり量(px)
OUT="output/final.mp4"

# 素材生成
if ! ls build/bg_*.png >/dev/null 2>&1; then python3 scripts/build_scenes.py; fi
mapfile -t BGS < <(ls -1 build/bg_*.png | sort)
N=${#BGS[@]}
TOTAL=$(( DISPLAY * (N - 1) + CLIP ))   # 全体尺
echo "シーン数:${N}  全体尺:${TOTAL}s"
mkdir -p output

# 入力（各シーン: 背景=単一フレーム / 文字=CLIP秒ループ）
# 背景は zoompan が d フレームを生成するため -loop を付けない（付けると激重）。
INPUTS=()
for ((i=0; i<N; i++)); do
  INPUTS+=(-i "build/bg_$(printf '%02d' "$i").png")
  INPUTS+=(-loop 1 -t "$CLIP" -i "build/tx_$(printf '%02d' "$i").png")
done

# フィルタ構築
PREP=""
for ((i=0; i<N; i++)); do
  bg=$((i*2)); tx=$((i*2+1))
  # 背景：1.25倍→ゆるくズーム→1080x1920
  PREP+="[${bg}:v]scale=1350:2400,zoompan=z='min(zoom+0.0004,1.05)':d=${FRAMES}:"
  PREP+="x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=${W}x${H}:fps=${FPS},setsar=1[bg${i}];"
  # 文字：フェードイン（アルファ）
  PREP+="[${tx}:v]format=rgba,fps=${FPS},setsar=1,fade=t=in:st=0:d=${INTRO}:alpha=1[tx${i}];"
  # 合成：頭でスライドアップ（y を時間で 0 に寄せる）
  PREP+="[bg${i}][tx${i}]overlay=x=0:y='${RISE}*(1-min(t/${INTRO}\,1))':format=auto,"
  PREP+="format=yuv420p,setsar=1[v${i}];"
done

# クロスフェード連結
CHAIN=""; PREV="[v0]"
for ((i=1; i<N; i++)); do
  OFF=$(( DISPLAY * i ))
  LBL="[x${i}]"; [[ "$i" -eq $((N-1)) ]] && LBL="[xf]"
  CHAIN+="${PREV}[v${i}]xfade=transition=fade:duration=${FADE}:offset=${OFF}${LBL};"
  PREV="$LBL"
done

# プログレスバー（下端・テラコッタ）
BAR="[xf]drawbox=x=0:y=${H}-8:w='iw*min(t/${TOTAL}\,1)':h=8:color=0xB04030@1.0:t=fill[outv]"

FILTER="${PREP}${CHAIN}${BAR}"

ffmpeg -y "${INPUTS[@]}" -filter_complex "$FILTER" -map "[outv]" \
  -r "$FPS" -c:v libx264 -pix_fmt yuv420p -profile:v high -preset veryfast -crf 18 \
  -movflags +faststart -an "$OUT"

echo "完成: $OUT"
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,pix_fmt,codec_name \
  -show_entries format=duration -of default=noprint_wrappers=1 "$OUT"
