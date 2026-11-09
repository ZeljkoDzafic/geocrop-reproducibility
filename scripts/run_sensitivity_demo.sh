#!/bin/sh
# End-to-end demo on SYNTHETIC samples: phenology features, A/B/C feature sets, partition-sensitivity CV, comparison table.
# Needs geocrop-engine >= 1.0.0rc2 (see requirements.txt). Usage: scripts/run_sensitivity_demo.sh [outdir]
set -e
GEOCROP=${GEOCROP:-geocrop}
PY=${PYTHON:-python3}
OUT=${1:-out}
mkdir -p "$OUT/pheno"
$PY synthetic/make_synthetic_dataset.py --out "$OUT/samples_synthetic.npz" --seed 7
$GEOCROP phenology-features --samples "$OUT/samples_synthetic.npz" --out "$OUT/samples_pheno.npz" \
  --sets-out "$OUT/feature_sets.json" --cutoffs 196 226 --windows P1=151 P2=196 P3=243 P4=273
SOY=$($PY - "$OUT/samples_synthetic.npz" <<'PYEOF'
import sys, numpy as np
d = np.load(sys.argv[1], allow_pickle=True)
print(" ".join(sorted(set(d["polygon"][d["y"] == "soybean"]))))
PYEOF
)
for grp in post_season in_season_d196 in_season_d226; do
  for s in A B C; do
    # shellcheck disable=SC2086
    $GEOCROP cv-stability --samples "$OUT/samples_pheno.npz" --feature-sets "$OUT/feature_sets.json" --feature-set "$grp:$s" \
      --block-sizes 3000 5000 --offsets 2 --n-estimators 100 --targets maize soybean sunflower --polygon-repeats 3 \
      --watch $SOY --out "$OUT/pheno/${grp}_$s" > "$OUT/pheno/${grp}_$s.log" 2>&1
  done
done
$PY scripts/compare_pheno.py --dir "$OUT/pheno" --atypical SOYBEAN_1 SOYBEAN_2 SOYBEAN_3
