"""Synthetic landscape, declared parcels and a simulated classifier, with KNOWN truth, for `geocrop crop-presence`.

No real parcels or declarations are used. The generator writes:

    probabilities.tif   simulated per-pixel class probabilities (forest, grass, maize, soybean, sunflower), 10 m
    parcels.gpkg        cadastral-like parcels: parcel_id, declared_crop, declared_area_ha
    truth.csv           parcel_id, truth_present (is the declared crop really on the parcel), true_crop_area_ha, ...

Parcels are heterogeneous: the declared crop (when present) fills a connected block of 20-100 % of the parcel, the rest is
forest or grass. About 25 % of the declarations are wrong by construction (another crop, or no crop) and some declared
areas are inflated. The simulated classifier is right for ~85 % of pixels, with isolated random errors, so the methods
can be compared with the truth. Numbers say nothing about real accuracy.

    python synthetic/make_synthetic_declarations.py --out out/declarations --seed 11
"""
import argparse
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box

CLASSES = ["forest", "grass", "maize", "soybean", "sunflower"]
CROPS = ["maize", "soybean", "sunflower"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out/declarations")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--accuracy", type=float, default=0.85, help="share of pixels the simulated classifier gets right")
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    rows_n, cols_n, cell = 8, 10, 25                  # 80 parcels in cells of 25 x 25 pixels (250 m)
    H, W = rows_n * cell, cols_n * cell
    truth_map = np.full((H, W), CLASSES.index("forest"), dtype=int)
    x0, y0, px = 500000.0, 5000000.0 + H * 10, 10.0
    recs, truth = [], []
    for r in range(rows_n):
        for c in range(cols_n):
            pid = f"S{r * cols_n + c + 1:03d}"
            r0, c0 = r * cell + 1, c * cell + 1
            h, w = 22, 22
            declared = str(rng.choice(CROPS))
            wrong = rng.random() < 0.25
            actual = declared
            if wrong:
                actual = str(rng.choice([k for k in CROPS if k != declared] + ["none"]))
            # background: forest/grass split by a vertical line
            parcel = np.full((h, w), CLASSES.index("forest"), dtype=int)
            split = int(rng.integers(3, w - 3))
            parcel[:, :split] = CLASSES.index("grass") if rng.random() < 0.6 else CLASSES.index("forest")
            crop_frac = float(rng.uniform(0.2, 1.0))
            if actual != "none":
                ch, cw = max(3, int(h * np.sqrt(crop_frac))), max(3, int(w * np.sqrt(crop_frac)))
                cr, cc = int(rng.integers(0, h - ch + 1)), int(rng.integers(0, w - cw + 1))
                parcel[cr:cr + ch, cc:cc + cw] = CLASSES.index(actual)
            truth_map[r0:r0 + h, c0:c0 + w] = parcel
            geom = box(x0 + c0 * px, y0 - (r0 + h) * px, x0 + (c0 + w) * px, y0 - r0 * px)
            true_ha = float((parcel == CLASSES.index(declared)).sum() * px * px / 1e4)
            declared_ha = round(true_ha * float(rng.uniform(0.9, 1.1)) if not wrong else
                                float(rng.uniform(0.3, 0.9) * h * w * px * px / 1e4), 3)
            if not wrong and rng.random() < 0.15:
                declared_ha = round(true_ha * 1.8, 3)                  # inflated declared area
            recs.append({"parcel_id": pid, "declared_crop": declared, "declared_area_ha": declared_ha, "geometry": geom})
            truth.append({"parcel_id": pid, "truth_present": bool(true_ha > 0), "true_crop_area_ha": true_ha,
                          "actual_crop": actual, "declaration_wrong_by_construction": wrong,
                          "parcel_area_ha": float(h * w * px * px / 1e4), "crop_share_of_parcel": true_ha / (h * w * px * px / 1e4)})
    # simulated classifier: right for `accuracy` of pixels, else a random other class; peaked probabilities
    k = len(CLASSES)
    pred = truth_map.copy()
    wrong_px = rng.random(truth_map.shape) > a.accuracy
    shift = rng.integers(1, k, size=truth_map.shape)
    pred[wrong_px] = (truth_map[wrong_px] + shift[wrong_px]) % k
    z = rng.dirichlet(np.ones(k) * 0.6, size=truth_map.shape).astype("float32").transpose(2, 0, 1) * 0.4
    peak = rng.uniform(0.45, 0.6, size=truth_map.shape).astype("float32")
    for i in range(k):
        z[i][pred == i] += peak[pred == i]
    z = z / z.sum(axis=0, keepdims=True)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out / "probabilities.tif", "w", driver="GTiff", height=H, width=W, count=k, dtype="float32",
                       crs="EPSG:32633", transform=from_origin(x0, y0, px, px)) as dst:
        dst.write(z.astype("float32"))
        dst.descriptions = CLASSES
    gpd.GeoDataFrame(recs, geometry="geometry", crs="EPSG:32633").to_file(out / "parcels.gpkg", driver="GPKG")
    pd.DataFrame(truth).to_csv(out / "truth.csv", index=False)
    print(f"wrote {out} ({len(recs)} parcels, {int(pd.DataFrame(truth).declaration_wrong_by_construction.sum())} wrong by construction)")


if __name__ == "__main__":
    main()
