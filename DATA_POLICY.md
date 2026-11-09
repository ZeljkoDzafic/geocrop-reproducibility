# Data policy

**Not distributed (and never will be in this repository):** the polygons of the manually delineated reference set, the
LPIS/RPG declarations of farmers, field observations and any per-polygon or per-parcel result (polygon identifiers with
predictions, out-of-fold tables, geometries). They are personal or administrative data held by the project partners.

**Distributed here**
- `synthetic/make_synthetic_dataset.py`: a generator of synthetic samples in the engine's `samples.npz` layout. It
  contains no real data. It places three soybean polygons with a maize-like, shorter season in one block to mimic the
  situation studied in the paper; the numbers it produces say nothing about real accuracy.
- `results_aggregate/`: aggregated results of the study (overall metrics per feature set and partition, partition
  spread, summary of all variants). No polygon identifiers, no geometries.
- `scenes/scenes_2023_imported.csv`: the Sentinel-2 and Sentinel-1 scenes imported for the study (public Copernicus
  data, with STAC links), so that the image side can be re-created from public sources.
- `configs/study_2023_resolved.yaml`, `aoi/`, `HASHES.md`: the resolved configuration of the 2023 run, the AOIs (boundaries only)
  and their hashes; reference-data paths in the configuration are placeholders.
- `results_aggregate/declared/`: aggregated results of the comparison with the declared-parcel layer (counts, shares, size
  classes of the components of a dissolved layer); the layer itself is not distributed.

**Access to the restricted data:** possible for qualified researchers on request to the corresponding author, subject to
the agreement of the data owners.
