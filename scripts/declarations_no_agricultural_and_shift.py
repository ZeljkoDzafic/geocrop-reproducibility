"""Declarations with (almost) no agricultural class on the E8 map, and a translation test of the declared geometries.
Aggregates only (no ids, no geometries) are written to aggregates/. Run with the engine venv."""
import json
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd, rasterio
from rasterio import features
from shapely import affinity
ROOT = Path(__file__).resolve().parents[2].parent if False else Path.home() / "Documents/geocrop-runs/lijevce_2023"
OUT = Path(__file__).resolve().parent / "aggregates"
res = pd.read_csv(Path(__file__).resolve().parent / "work/E8_noseg/crop_presence.csv")
LEG = {int(k): v for k, v in json.load(open(ROOT / "out/prediction/class_legend.json")).items()}
AGRI = {"maize", "soybean", "sunflower", "vegetables", "winter_crops"}
# 1. declarations with < 10 % of the parcel mapped as agricultural
res["agri_share"] = res.agricultural_area_ha / (res.agricultural_area_ha + res.non_agricultural_area_ha)
low = res[res.agri_share <= 0.1].copy()
print("rows", len(res), "low agri", len(low), "no valid px", int(res.agri_share.isna().sum()))
bins = [0, 0.1, 0.2, 0.5, 1, 2, 1e9]; labels = ["<0.1", "0.1-0.2", "0.2-0.5", "0.5-1", "1-2", ">=2"]
res["size_class"] = pd.cut(res.parcel_area_ha, bins, labels=labels, right=False)
low["size_class"] = pd.cut(low.parcel_area_ha, bins, labels=labels, right=False)
t = pd.DataFrame({"size_class_ha": labels,
                  "declarations": [int((res.size_class == l).sum()) for l in labels],
                  "low_agri_declarations": [int((low.size_class == l).sum()) for l in labels]})
t["share_low_agri"] = t.low_agri_declarations / t.declarations
t.to_csv(OUT / "no_agricultural_class_by_size.csv", index=False); print(t.to_string(index=False))
share_cols = [c for c in low.columns if c.startswith("share_")]
comp = (low[share_cols].mean()).rename("mean_share_of_parcel").reset_index().rename(columns={"index": "class"})
comp["class"] = comp["class"].str.replace("share_", "")
comp.to_csv(OUT / "no_agricultural_class_composition.csv", index=False); print(comp.round(3).to_string(index=False))
# 2. translation test of the geometries (pixel centres inside the translated geometry, pixel-weighted)
g = gpd.read_file(Path(__file__).resolve().parent / "work/parcels_neutral.gpkg")
with rasterio.open(ROOT / "out/prediction/classes.tif") as r:
    c = r.read(1); tr = r.transform; crs = r.crs; shape = c.shape
g = g.to_crs(crs)
valid = c != 255
agri_ids = [k for k, v in LEG.items() if v in AGRI]
crop_id = {v: k for k, v in LEG.items()}
dec = g["declared_crop"].map(crop_id).to_numpy()
def run(dx, dy):
    shapes = [(affinity.translate(geom, dx, dy), int(i + 1)) for i, geom in enumerate(g.geometry)]
    ids = features.rasterize(shapes, out_shape=shape, transform=tr, fill=0, dtype="int32")   # overlaps: last declaration wins
    m = (ids > 0) & valid
    cls = c[m]; own = dec[ids[m] - 1]
    return float(np.isin(cls, agri_ids).mean()), float((cls == own).mean()), int(m.sum())
rows = []
for d in (0, 30, 60, 100, 200):
    for name, (dx, dy) in {"E": (d, 0), "W": (-d, 0), "N": (0, d), "S": (0, -d)}.items():
        if d == 0 and name != "E": continue
        a, o, n = run(dx, dy); rows.append({"shift_m": d, "direction": name if d else "none", "share_pixels_mapped_agricultural": a,
                                           "share_pixels_mapped_as_declared_crop": o, "pixels": n})
s = pd.DataFrame(rows); s.to_csv(OUT / "translation_test.csv", index=False)
print(s.groupby("shift_m")[["share_pixels_mapped_agricultural", "share_pixels_mapped_as_declared_crop"]].agg(["min", "max"]).round(3).to_string())
