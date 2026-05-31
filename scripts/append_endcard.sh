#!/usr/bin/env bash
#
# append_endcard.sh ― 無音リール末尾に QRエンドカードをクロスフェード追加し、
#                     BGM を付け直して output/final.mp4 を書き出す。
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(cd "$SCRIPT_DIR/.." && pwd)"

W=1080; H=1920; FPS=30; FADE=1; HOLD=4
SIL="output/final_silent.mp4"
CARD="build/endcard.png"
BGM="audio/Oden_nou.mp3"
TMP="output/_with_card.mp4"
OUT="output/final.mp4"

[[ -f "$SIL"  ]] || { echo "no $SIL";  exit 1; }
[[ -f "$CARD" ]] || python3 scripts/build_endcard.py
[[ -f "$BGM"  ]] || { echo "no $BGM";  exit 1; }

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$SIL")
OFF=$(awk -v d="$DUR" -v f="$FADE" 'BEGIN{printf "%.3f", d-f}')
echo "無音尺=${DUR}s  xfade offset=${OFF}s"

ffmpeg -y -i "$SIL" -loop 1 -t "$HOLD" -i "$CARD" \
  -filter_complex "\
[0:v]fps=${FPS},format=yuv420p,setsar=1[v0];\
[1:v]scale=${W}:${H},fps=${FPS},format=yuv420p,setsar=1[v1];\
[v0][v1]xfade=transition=fade:duration=${FADE}:offset=${OFF}[outv]" \
  -map "[outv]" -r "$FPS" -c:v libx264 -pix_fmt yuv420p -profile:v high -preset veryfast -crf 18 \
  -movflags +faststart -an "$TMP"

VDUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$TMP")
FOUT=$(awk -v d="$VDUR" 'BEGIN{printf "%.2f", (d-1.5>0)?d-1.5:0}')
ffmpeg -y -i "$TMP" -i "$BGM" \
  -filter_complex "[1:a]afade=t=in:st=0:d=0.8,afade=t=out:st=${FOUT}:d=1.5,volume=0.9[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 44100 -shortest -movflags +faststart "$OUT"
rm -f "$TMP"

echo "完成: $OUT"
ffprobe -v error -show_entries stream=codec_type,codec_name -show_entries format=duration \
  -of default=noprint_wrappers=1 "$OUT"
