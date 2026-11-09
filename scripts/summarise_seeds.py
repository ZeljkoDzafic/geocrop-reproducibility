"""Run the crop-presence synthetic demo for many seeds and summarise the spread (one simulation is not a distribution).

    python scripts/summarise_seeds.py --seeds 20 --out out/seeds   (needs GEOCROP and PYTHON like the demo script)
"""
import argparse
import os
import subprocess
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--out", default="out/seeds")
    a = ap.parse_args()
    frames = []
    for seed in range(1, a.seeds + 1):
        d = Path(a.out) / f"seed_{seed}"
        subprocess.run(["scripts/run_crop_presence_demo.sh", str(d)], env={**os.environ, "SEED": str(seed)}, check=True,
                       stdout=subprocess.DEVNULL)
        t = pd.read_csv(d / "crop_presence_synthetic_scores.csv")
        t["seed"] = seed
        frames.append(t)
    allr = pd.concat(frames)
    allr.to_csv(Path(a.out) / "all_seeds.csv", index=False)
    g = allr.groupby(["method", "subset"])
    summ = g.agg(seeds=("seed", "nunique"), correct_declarations_mean=("correct_declarations", "mean"),
                 recall_mean=("recall_of_correct", "mean"), recall_min=("recall_of_correct", "min"), recall_max=("recall_of_correct", "max"),
                 wrong_declarations_mean=("wrong_declarations", "mean"), wrongly_supported_mean=("wrongly_supported", "mean"),
                 wrongly_supported_min=("wrongly_supported", "min"), wrongly_supported_max=("wrongly_supported", "max")).reset_index()
    summ.to_csv(Path(a.out) / "summary_over_seeds.csv", index=False)
    print(summ.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
