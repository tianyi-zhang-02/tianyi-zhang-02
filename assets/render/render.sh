#!/usr/bin/env bash
# Renders the four background pictures into this folder. Intermediate arrays go to a temporary directory.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
BH="ROLL=-22 STREAM=1.2 ROUT=15 SS=3"            # the hole: tilted, with a red stream, 3x3 rays per pixel
ICE="LBACK=1.8 TEX=1.6 SS=3"                       # the planet: back-lit ice

picture() {  # name, sky size W H, sky settings, planet settings, compose settings
  local name=$1 w=$2 h=$3 sky=$4 planet=$5 comp=$6
  env $BH $sky python3 "$HERE/raytrace.py" $((w * 3)) $((h * 3)) "$T/$name-sky.npy" 9 60
  env $ICE $planet python3 "$HERE/planet.py" "$w" "$h" "$T/$name-planet"
  env GLOW=0 $comp python3 "$HERE/compose.py" "$T/$name-sky.npy" "$T/$name-planet" "$T/$name"
  cp "$T/$name.jpg" "$HERE/$name.jpg"
}

picture banner        2400 1000 "HX=.5 HY=.28 SHADOW=84"   "KS=1.2 PR=2600 TOP=.835"           ""
picture banner-mobile 1200 1360 "HX=.5 HY=.27 SHADOW=150"  "KS=1.2 PR=2600 TOP=.855"           ""
picture card          1760 400  "HX=.84 HY=.36 SHADOW=27"  "KS=1.0 PR=1700 TOP=.80 LX=.66 FWD=.30" "LX=.66"
picture card-mobile   1200 540  "HX=.80 HY=.25 SHADOW=36"  "KS=1.0 PR=1100 TOP=.86 LX=.62 FWD=.34" "LX=.62"
