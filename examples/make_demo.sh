#!/usr/bin/env bash
# Generate a synthetic demo track and render a lyrics video from it.
# Usage: ./examples/make_demo.sh [theme]
set -euo pipefail
cd "$(dirname "$0")/.."

THEME="${1:-midnight}"
AUDIO="output/demo-tone.m4a"
mkdir -p output

# 32 s of gentle synth chords so there is something to hear (and a waveform to draw).
ffmpeg -y -hide_banner -loglevel error -f lavfi \
  -i "sine=frequency=220:duration=32" -f lavfi -i "sine=frequency=277:duration=32" \
  -f lavfi -i "sine=frequency=330:duration=32" \
  -filter_complex "[0:a][1:a][2:a]amix=inputs=3,volume=0.5,tremolo=f=0.5:d=0.6[a]" \
  -map "[a]" -c:a aac "$AUDIO"

python3 -m lyricsvideo render "$AUDIO" examples/demo.lrc \
  --theme "$THEME" --waveform --quiet -o "output/demo-$THEME.mp4"

echo "Done: output/demo-$THEME.mp4"
