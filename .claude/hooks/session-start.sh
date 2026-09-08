#!/bin/bash
# SessionStart hook — prepares the Lyrics Videos toolchain in Claude Code on
# the web so every session starts render-ready (see README "Remote sandbox
# setup"). Idempotent: each step is skipped when its result already exists,
# so cached containers start fast.
set -uo pipefail

# Local machines are assumed to be set up already.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

status=()
warn() { echo "session-start WARNING: $*" >&2; }

# ---------------------------------------------------------------------------
# 1. ffmpeg + ffprobe — apt is blocked by the network policy; GitHub release
#    assets pass the proxy, so use BtbN's static build.
# ---------------------------------------------------------------------------
if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
  status+=("ffmpeg: already installed")
else
  tmp=$(mktemp -d)
  if curl -fsSL --retry 3 -o "$tmp/ffmpeg.tar.xz" \
      "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz" \
      && tar -xJf "$tmp/ffmpeg.tar.xz" -C "$tmp"; then
    install -m 0755 "$tmp"/ffmpeg-*/bin/ffmpeg "$tmp"/ffmpeg-*/bin/ffprobe /usr/local/bin/
    status+=("ffmpeg: installed static build")
  else
    warn "ffmpeg download failed — renders will not work until it is installed"
    status+=("ffmpeg: MISSING (download failed)")
  fi
  rm -rf "$tmp"
fi

# ---------------------------------------------------------------------------
# 2. Brand fonts — dynamic: install every font family referenced by any
#    brands/*.json (any key containing "font"), plus any families listed in
#    brands/extra-fonts.txt (one Google Fonts family name per line, '#'
#    comments allowed). Adding a brand or stocking up on fonts needs no hook
#    change. Fetching Google Fonts CSS without a browser UA yields TTF URLs.
#
#    A brand may name a specific weight as its own family, e.g. Vasos de
#    Barro's "Crimson Pro SemiBold" / "Crimson Pro Black" (fontconfig
#    registers those named instances, and ASS can only toggle bold, so a
#    third weight has to be addressed by name). Google Fonts has no such
#    family — only "Crimson Pro" at weight 600/900 — so a trailing style
#    word is split off into a weight and the base family is fetched with
#    every weight anyone asks for. extra-fonts.txt may also request
#    weights explicitly as "Family:400,700,900".
# ---------------------------------------------------------------------------
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"

# "Base Family|weights" per line (weights comma-separated), deduplicated.
font_families=$(python3 - "$PROJECT_DIR" <<'PY'
import json, sys
from pathlib import Path

# Style words that name a weight instance rather than a Google family.
WEIGHTS = {
    "thin": 100, "extralight": 200, "ultralight": 200, "light": 300,
    "regular": 400, "normal": 400, "medium": 500, "semibold": 600,
    "demibold": 600, "bold": 700, "extrabold": 800, "ultrabold": 800,
    "black": 900, "heavy": 900,
}

root = Path(sys.argv[1])
wanted: dict[str, set[int]] = {}


def add(name: str, weights=None):
    name = name.strip()
    if not name:
        return
    if weights is None:
        # Split a trailing style word off the family name ("Crimson Pro
        # SemiBold" -> family "Crimson Pro", weight 600). Two-word styles
        # ("Extra Bold") collapse once spaces are removed.
        parts = name.split()
        for take in (2, 1):
            if len(parts) > take:
                key = "".join(parts[-take:]).lower()
                if key in WEIGHTS:
                    name = " ".join(parts[:-take])
                    weights = {WEIGHTS[key]}
                    break
    # Regular and bold are always useful: ASS toggles bold on any style.
    wanted.setdefault(name, set()).update(weights or set())
    wanted[name].update({400, 700})


for p in sorted((root / "brands").glob("*.json")):
    try:
        brand = json.loads(p.read_text())
    except Exception:
        continue
    for key, val in brand.items():
        if "font" in key.lower() and isinstance(val, str):
            add(val)

extra = root / "brands" / "extra-fonts.txt"
if extra.is_file():
    for line in extra.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        family, _, spec = line.partition(":")
        explicit = {int(w) for w in spec.replace(",", " ").split() if w.strip().isdigit()}
        add(family, explicit or None)

for family in sorted(wanted):
    print(f"{family}|" + ",".join(str(w) for w in sorted(wanted[family])))
PY
)

install_font_family() {
  local family="$1" weights="$2"
  local plus="${family// /+}"
  local css urls u n=0 ital spec
  # A family is "installed" only with all its requested weights on disk, so
  # the stamp records the set — asking for a new weight re-runs the install.
  local stamp="$HOME/.fonts/.installed-${family// /-}-${weights//,/_}"
  [ -f "$stamp" ] && return 0

  # Ask for every requested weight in both styles, then fall back to
  # narrower specs: a family that lacks a weight (or the italic axis)
  # answers 400 to the precise request but still serves the basics.
  spec=""
  for ital in 0 1; do
    local w
    for w in ${weights//,/ }; do
      spec="${spec:+$spec;}${ital},${w}"
    done
  done

  for attempt in "${plus}:ital,wght@${spec}" \
                 "${plus}:wght@${weights//,/;}" \
                 "${plus}:ital,wght@0,400;0,700;1,400;1,700" \
                 "${plus}"; do
    css=$(curl -fsSL "https://fonts.googleapis.com/css2?family=${attempt}") && [ -n "$css" ] && break
    css=""
  done
  [ -n "$css" ] || return 1

  urls=$(printf '%s' "$css" | grep -oE 'https://fonts\.gstatic\.com/[^)]+\.ttf' | sort -u)
  [ -n "$urls" ] || return 1
  mkdir -p "$HOME/.fonts"
  for u in $urls; do
    curl -fsSL --retry 2 -o "$HOME/.fonts/${family// /-}-$n.ttf" "$u" && n=$((n + 1))
  done
  [ "$n" -gt 0 ] || return 1
  touch "$stamp"
}

fonts_ok=""
fonts_bad=""
while IFS= read -r entry; do
  [ -n "$entry" ] || continue
  family="${entry%%|*}"
  weights="${entry##*|}"
  if install_font_family "$family" "$weights"; then
    fonts_ok="${fonts_ok:+$fonts_ok, }$family ($weights)"
  else
    fonts_bad="${fonts_bad:+$fonts_bad, }$family"
  fi
done <<< "$font_families"
fc-cache -f >/dev/null 2>&1 || true
[ -n "$fonts_ok" ] && status+=("fonts available: $fonts_ok")
if [ -n "$fonts_bad" ]; then
  warn "font install failed for: $fonts_bad — check fc-list before rendering"
  status+=("fonts MISSING: $fonts_bad")
fi

# ---------------------------------------------------------------------------
# 3. Python package + deps (renderer is stdlib-only; extras cover
#    transcription, thumbnails, and reading the lyrics PDFs).
# ---------------------------------------------------------------------------
if pip install -q -e "${CLAUDE_PROJECT_DIR:-.}" sherpa-onnx numpy pillow pypdf; then
  status+=("python: lyricsvideo + sherpa-onnx/numpy/pillow/pypdf installed")
else
  warn "pip install failed"
  status+=("python: pip install FAILED")
fi

# ---------------------------------------------------------------------------
# 4. Offline Whisper models for `lyricsvideo transcribe` (sherpa-onnx
#    backend; large download, but the container cache keeps it warm).
# ---------------------------------------------------------------------------
MODELS_DIR="/home/user/models"
if [ -f "$MODELS_DIR/silero_vad.onnx" ] && ls -d "$MODELS_DIR"/sherpa-onnx-whisper-*/ >/dev/null 2>&1; then
  status+=("whisper models: already present in $MODELS_DIR")
else
  mkdir -p "$MODELS_DIR"
  models_ok=true
  [ -f "$MODELS_DIR/silero_vad.onnx" ] || curl -fsSL --retry 3 -o "$MODELS_DIR/silero_vad.onnx" \
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx" || models_ok=false
  if ! ls -d "$MODELS_DIR"/sherpa-onnx-whisper-*/ >/dev/null 2>&1; then
    if curl -fsSL --retry 3 -o "$MODELS_DIR/whisper-turbo.tar.bz2" \
        "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-turbo.tar.bz2" \
        && tar -xjf "$MODELS_DIR/whisper-turbo.tar.bz2" -C "$MODELS_DIR"; then
      rm -f "$MODELS_DIR/whisper-turbo.tar.bz2"
    else
      rm -f "$MODELS_DIR/whisper-turbo.tar.bz2"
      models_ok=false
    fi
  fi
  if $models_ok; then
    status+=("whisper models: downloaded to $MODELS_DIR")
  else
    warn "whisper model download incomplete — transcription of NEW songs unavailable (existing .lrc files unaffected)"
    status+=("whisper models: INCOMPLETE (only needed to transcribe new songs)")
  fi
fi

if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "export LYRICSVIDEO_SHERPA_MODELS=$MODELS_DIR" >> "$CLAUDE_ENV_FILE"
fi

echo "Lyrics Videos environment setup:"
printf ' - %s\n' "${status[@]}"
