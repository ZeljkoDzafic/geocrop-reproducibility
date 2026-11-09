#!/bin/sh
# Synthetic demo with known truth: simulated classifier, declared parcels, geocrop crop-presence, scoring.
# SEED (default 11) selects the synthetic landscape. Needs a GeoCrop Engine that contains `crop-presence` (see requirements-crop-presence.txt). Usage: scripts/run_crop_presence_demo.sh [outdir]
set -e
GEOCROP=${GEOCROP:-geocrop}
PY=${PYTHON:-python3}
OUT=${1:-out}
SEED=${SEED:-11}
$PY synthetic/make_synthetic_declarations.py --out "$OUT/declarations" --seed "$SEED"
$GEOCROP crop-presence --probabilities "$OUT/declarations/probabilities.tif" --parcels "$OUT/declarations/parcels.gpkg" \
  --declared-area-field declared_area_ha --out "$OUT/crop_presence" > "$OUT/crop_presence.log"
$PY scripts/compare_crop_presence.py --presence "$OUT/crop_presence/crop_presence.csv" --truth "$OUT/declarations/truth.csv" --out-csv "$OUT/crop_presence_synthetic_scores.csv"
