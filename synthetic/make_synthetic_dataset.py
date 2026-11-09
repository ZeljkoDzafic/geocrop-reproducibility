"""Synthetic reference samples for the GeoCrop sensitivity workflow. No real field or parcel data are used.

Writes a samples file in the engine's `samples.npz` layout: nine classes, polygons placed on a synthetic 30 x 30 km
area (EPSG:32633 coordinates), class-specific seasonal NDVI/NDRE curves on a 15-day grid, window features P1-P4,
deltas and whole-season summaries. Three soybean polygons are given a maize-like, shorter and earlier season and
are placed in one 5 km block, to mimic the situation studied in the paper (labels correct, development atypical).
The curves are stylised and the numbers it produces say nothing about real accuracy.

    python synthetic/make_synthetic_dataset.py --out data/samples_synthetic.npz --seed 7
"""
import argparse
import json
from pathlib import Path

import numpy as np

DAYS = np.arange(91, 272, 15)                         # ts_<index>_d<doy> grid
WINDOWS = {"P1": (91, 151), "P2": (152, 196), "P3": (197, 243), "P4": (244, 273)}
# class -> (peak_doy, peak_value, width_days, base); stylised curves
CLASSES = {"winter_crops": (140, 0.85, 45, 0.25), "maize": (205, 0.82, 38, 0.20), "soybean": (228, 0.88, 36, 0.18),
           "sunflower": (195, 0.78, 33, 0.20), "vegetables": (190, 0.60, 50, 0.25), "grass": (180, 0.70, 140, 0.55),
           "forest": (190, 0.88, 160, 0.70), "water": (180, 0.05, 200, -0.05), "built_up": (180, 0.22, 200, 0.18)}
COUNTS = {"winter_crops": 15, "maize": 45, "soybean": 39, "sunflower": 25, "vegetables": 13, "grass": 45, "forest": 21,
          "water": 9, "built_up": 39}


def curve(peak, height, width, base, rng, shift=0.0, scale=1.0):
    c = base + (height - base) * np.exp(-0.5 * ((DAYS - (peak + shift)) / width) ** 2)
    return np.clip(c * scale + rng.normal(0, 0.012, len(DAYS)), -0.2, 1.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/samples_synthetic.npz")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--pixels", type=int, default=20, help="pixels per polygon")
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    rows, y, poly, xs, ys = [], [], [], [], []
    names = None
    atypical = {"soybean": 3}
    odd_block = (12000, 17000, 22000, 27000)             # 5 km block (x0, x1, y0, y1) of the three atypical polygons
    for cls, n in COUNTS.items():
        pk, h, w, b = CLASSES[cls]
        for k in range(n):
            pid = f"{cls.upper()}_{k + 1}"
            odd = cls in atypical and k < atypical[cls]
            if odd:
                cx, cy = rng.uniform(odd_block[0] + 500, odd_block[1] - 500), rng.uniform(odd_block[2] + 500, odd_block[3] - 500)
                pkx, hx, wx = 205 + rng.normal(0, 3), 0.80, 26                       # maize-like peak, shorter season
            else:
                cx, cy = rng.uniform(0, 30000), rng.uniform(0, 30000)
                pkx, hx, wx = pk + rng.normal(0, 5), h, w
            poly_shift = rng.normal(0, 4)
            for _ in range(a.pixels):
                px, py = cx + rng.normal(0, 60), cy + rng.normal(0, 60)
                ndvi = curve(pkx, hx, wx, b, rng, poly_shift)
                ndre = np.clip(0.55 * ndvi + 0.05 + rng.normal(0, 0.01, len(DAYS)), -0.2, 1.0)
                feats = {}
                for wn, (d0, d1) in WINDOWS.items():
                    m = (DAYS >= d0) & (DAYS <= d1)
                    if not m.any():
                        m = DAYS == DAYS[np.abs(DAYS - (d0 + d1) / 2).argmin()]
                    feats[f"{wn}_NDVI"], feats[f"{wn}_NDRE"] = ndvi[m].mean(), ndre[m].mean()
                    feats[f"{wn}_B08"] = 0.25 + 0.3 * feats[f"{wn}_NDVI"] + rng.normal(0, 0.01)
                    feats[f"{wn}_B04"] = 0.12 - 0.08 * feats[f"{wn}_NDVI"] + rng.normal(0, 0.005)
                    feats[f"{wn}_VH_dB"] = -20 + 4 * feats[f"{wn}_NDVI"] + rng.normal(0, 0.6)
                ks = list(WINDOWS)
                for p0, p1 in zip(ks[:-1], ks[1:]):
                    feats[f"delta_NDVI_{p0}_{p1}"] = feats[f"{p1}_NDVI"] - feats[f"{p0}_NDVI"]
                feats["season_NDVI_max"], feats["season_NDVI_min"] = ndvi.max(), ndvi.min()
                feats["season_NDVI_argmax"] = float(DAYS[ndvi.argmax()])
                for d, v in zip(DAYS, ndvi):
                    feats[f"ts_NDVI_d{d}"] = v
                for d, v in zip(DAYS, ndre):
                    feats[f"ts_NDRE_d{d}"] = v
                names = names or list(feats)
                rows.append([feats[n] for n in names])
                y.append(cls); poly.append(pid); xs.append(px); ys.append(py)
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, X=np.array(rows, dtype="float32"), y=np.array(y), polygon=np.array(poly),
                        x=np.array(xs) + 400000.0, yy=np.array(ys) + 5000000.0, features=np.array(names),
                        crs="EPSG:32633", reference_classes=np.array(sorted(COUNTS)))
    atyp = [f"SOYBEAN_{k + 1}" for k in range(atypical["soybean"])]
    out.with_suffix(".json").write_text(json.dumps({"synthetic": True, "seed": a.seed, "atypical_soybean_polygons": atyp,
                                                    "windows_end_doy": {k: v[1] for k, v in WINDOWS.items()},
                                                    "n_samples": len(y), "n_features": len(names)}, indent=1))
    print(f"wrote {out} ({len(y)} samples, {len(names)} features); atypical polygons: {atyp}")


if __name__ == "__main__":
    main()
