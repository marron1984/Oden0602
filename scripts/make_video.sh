#!/usr/bin/env bash
#
# make_video.sh
# 梅田エリアの写真から Instagram リール用の縦型スライドショー動画を生成する。
#
# テーマ：①第1木曜 興味喚起（入口）/ 季節・世界観・空気感
#  - あえて売らない、保存・印象重視の構成
#  - 写真の流れ：梅田モニュメント → EST周辺の施設 → 街並み → おでん店
#
# 仕様:
#   - 出力先          : output/final.mp4
#   - 解像度          : 1080x1920（縦型 9:16 / インスタリール）
#   - 1枚の表示時間   : 3秒
#   - 切り替え        : クロスフェード 1秒
#   - フレームレート  : 30fps
#   - 映像コーデック  : H.264 (libx264)
#   - ピクセル形式    : yuv420p（インスタ互換）
#   - 音声           : なし
#
# 縦横比がバラバラな写真も 9:16 にフィットさせ、余白は黒で埋める。
#
set -euo pipefail

# このスクリプトの場所を基準にリポジトリのルートへ移動
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# ---- パラメータ ----
W=1080            # 横幅
H=1920            # 高さ（9:16）
FPS=30            # フレームレート
DISPLAY=3         # 1枚あたりの表示秒数
FADE=1            # クロスフェード秒数
OUT="output/final.mp4"

mkdir -p output

# ---- 入力写真の収集（ファイル名昇順）----
mapfile -t IMAGES < <(ls -1 IMG_*.jpg 2>/dev/null | sort)
N=${#IMAGES[@]}
if [[ "$N" -eq 0 ]]; then
  echo "エラー: IMG_*.jpg が見つかりません。" >&2
  exit 1
fi
echo "対象写真: ${N} 枚"

# 1クリップの長さ = 表示時間 + フェード時間（フェードは前後クリップで重なる）
CLIP=$((DISPLAY + FADE))

# ---- filter_complex を組み立てる ----
INPUTS=()
PREP=""
for i in "${!IMAGES[@]}"; do
  # 各画像を静止画クリップとして読み込む
  INPUTS+=(-loop 1 -t "$CLIP" -i "${IMAGES[$i]}")
  # 9:16 にフィット（アスペクト維持で縮小）→ 黒で余白埋め → 30fps / yuv420p
  PREP+="[${i}:v]scale=${W}:${H}:force_original_aspect_ratio=decrease,"
  PREP+="pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2:color=black,"
  PREP+="setsar=1,fps=${FPS},format=yuv420p[v${i}];"
done

# xfade チェーンを構築
CHAIN=""
if [[ "$N" -eq 1 ]]; then
  # 写真が1枚だけの場合はそのまま
  CHAIN="[v0]copy[outv];"
  LAST="[outv]"
else
  PREV="[v0]"
  for ((i=1; i<N; i++)); do
    OFFSET=$(( DISPLAY * i ))   # i 番目の切り替え開始位置 = 表示秒 × i
    if [[ "$i" -eq $((N-1)) ]]; then
      LABEL="[outv]"
    else
      LABEL="[x${i}]"
    fi
    CHAIN+="${PREV}[v${i}]xfade=transition=fade:duration=${FADE}:offset=${OFFSET}${LABEL};"
    PREV="${LABEL}"
  done
  LAST="[outv]"
fi

FILTER="${PREP}${CHAIN}"
FILTER="${FILTER%;}"   # 末尾のセミコロンを除去

# ---- ffmpeg 実行 ----
ffmpeg -y "${INPUTS[@]}" \
  -filter_complex "$FILTER" \
  -map "$LAST" \
  -r "$FPS" \
  -c:v libx264 -pix_fmt yuv420p -profile:v high -preset medium -crf 20 \
  -movflags +faststart \
  -an \
  "$OUT"

echo "完成: $OUT"
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,pix_fmt,codec_name \
  -show_entries format=duration -of default=noprint_wrappers=1 "$OUT"
