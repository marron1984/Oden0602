#!/usr/bin/env bash
#
# add_bgm.sh ―  リール映像に BGM（audio/Oden.mp3）を付ける。
#   - 動画の長さに合わせて BGM をトリム
#   - フェードイン(0.8s) / フェードアウト(1.5s)
#   - AAC 192k で多重化（映像は再エンコードせずコピー）
#
# 入力 : output/final_silent.mp4（無音の映像） + audio/Oden.mp3
# 出力 : output/final.mp4
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(cd "$SCRIPT_DIR/.." && pwd)"

VID="output/final_silent.mp4"
BGM="audio/Oden_nou.mp3"
OUT="output/final.mp4"

[[ -f "$VID" ]] || { echo "no $VID"; exit 1; }
[[ -f "$BGM" ]] || { echo "no $BGM"; exit 1; }

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VID")
FOUT=$(awk -v d="$DUR" 'BEGIN{printf "%.2f", (d-1.5>0)?d-1.5:0}')
echo "映像尺=${DUR}s / フェードアウト開始=${FOUT}s"

ffmpeg -y -i "$VID" -i "$BGM" \
  -filter_complex "[1:a]afade=t=in:st=0:d=0.8,afade=t=out:st=${FOUT}:d=1.5,volume=0.9[a]" \
  -map 0:v -map "[a]" \
  -c:v copy -c:a aac -b:a 192k -ar 44100 \
  -shortest -movflags +faststart \
  "$OUT"

echo "完成: $OUT"
ffprobe -v error -show_entries stream=codec_type,codec_name -show_entries format=duration \
  -of default=noprint_wrappers=1 "$OUT"
