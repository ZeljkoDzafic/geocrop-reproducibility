# Aggregated results of the second analysis round (Tables 13–15 of the paper)

Counts and shares only; no parcel or polygon identifiers, cadastral keys or geometries ([DATA_POLICY.md](../../DATA_POLICY.md)).
All numbers are model outputs on 4,998 declarations of 2023, satellite consistency and not accuracy: there is no
field verification, and the thresholds are starting values that are **not validated**. They are a recommendation for
human review, not a definitive conclusion.

## What supports which table

| Table / statement | Files |
|---|---|
| Table 13 (P1/P2/P3, presence and mismatch categories on all declarations, ≥ 0.2 ha, ≥ 0.5 ha and geometrically suitable parcels); Table 14 (primary mismatch reason, columns `mm_*`) | `table14_subsets_E8.csv` (E8 map), `table14_subsets_E0.csv` (E0 map), `by_size_E8.csv`, `by_crop_E8.csv`, `suitability/subset_comparison.csv`, `suitability/subset_agreement.csv` |
| Geometric suitability (36.1 % pass, reasons, exclusions by crop, sensitivity to the width, area and inner-pixel thresholds) | `suitability/suitability_reasons_E8.csv`, `suitability/subset_excluded.csv`, `suitability/subset_excluded_by_crop.csv`, `suitability/suitability_sensitivity.csv` |
| Presence criterion against P1/P2/P3 and its sensitivity to the minimum connected area and support probability | `presence/presence_x_p3_E8.csv`, `presence/presence_sensitivity_E8.csv` |
| Declarations with at most 10 % agricultural pixels | `lowagri_counts_E8.csv`, `lowagri_dominant_class_E8.csv` |
| Table 15 (segment density 100, 300, 500, 1,000 per km²) | `segment_density/segment_density_summary.csv` |

Column definitions follow the engine documentation (`geocrop crop-presence`, `geocrop parcel-suitability`, `geocrop segmentation-sweep`).

## How the numbers were produced

Engine: the analyses were run with the code of commit `bb5f1bd` (release v1.0.0rc4), which contains the commit of the
suitability, presence and window modules (`4ac1265`). The archived release that contains all of it is v1.0.0rc5 (commit
`7ade928`, Zenodo DOI 10.5281/zenodo.24156741; all versions 10.5281/zenodo.24078244). Release v1.0.0rc5 adds warnings to
the segment-density sweep and changes the wording of the suitability output; no result changes. The run manifests of the earlier analyses report `engine_version` 1.0.0rc3 because the installed package
metadata of the working environment was out of date, not because rc3 code was used.

Inputs (SHA-256):
- E8 probability raster (`probabilities.tif` of the clean re-execution): `4420898d8e360034008494e5b2870dfecbe5b957c1eb683624670ab79476b1c2`
- declarations layer with the neutral columns (`parcel_id`, `declared_crop`, `declared_area_ha`; not distributed): `3705d5001d107e517db8c4c7841896db483b4b7da64a1c4faf6b34979c2c3eb1`
- feature stack used for the segmentation (`stack_2023.tif`, bands `P3_B04 P3_B08 P3_B11 P3_NDVI`): `53374014912a73d655e0a01d5976ff469e4126beeb0a3cdd518834663d169314`
- AOI mask (`grid_10m_aoi.tif`): `89a1e35de032ba8e76f8e9e6df6a3788d9b1e8394dad9c286a2c26520082912c`

Commands (paths are placeholders):

```
# presence status, P1/P2/P3 and mismatch categories (Table 13, 14); baseline: segments = connected pixels of one class
geocrop crop-presence --probabilities probabilities.tif --parcels declarations.gpkg --declared-area-field declared_area_ha \
  --sensitivity --out presence_E8
# geometric suitability and the comparison on subsets (grid: width 40/50/60 m, 4/10/16/25 inner pixels)
geocrop parcel-suitability --parcels declarations.gpkg --raster probabilities.tif --declared-field declared_crop \
  --crop-presence presence_E8/crop_presence.csv --inner-buffer-m 10 --min-area-ha 0.2 --min-width-m 50 --min-inner-pixels 10 \
  --grid-areas 0.2 --grid-widths 40 50 60 --grid-inner-pixels 4 10 16 25 --p2-threshold 0.5 --out suitability_E8
# Table 15: segments per density, then crop-presence on each set of segments with the settings above
geocrop segment-obia --raster stack_2023.tif --bands P3_B04 P3_B08 P3_B11 P3_NDVI --compactness 10 \
  --aoi-mask grid_10m_aoi.tif --workers 1 --segments-per-km2 <100|300|500> --out segments_d<density>.gpkg
geocrop segment-obia ... --tile-size 512 --min-area-pixels 1 --segments-per-km2 1000 --out segments_d1000.gpkg
geocrop crop-presence --probabilities probabilities.tif --parcels declarations.gpkg --declared-area-field declared_area_ha \
  --segments segments_d<density>.gpkg --out presence_d<density>
```

The options used are recorded in the run manifests (`inner_buffer_m` 10, `min_area_ha` 0.2, `min_width_m` 50, `min_inner_pixels` 10, `width_method` inscribed). The segment commands were run on the AOI only (`--aoi-mask`); check the option names with `geocrop <command> --help` of the release.

## Limits of Table 15

The densities 100 to 500 used tiles of 1,024 pixels and a minimum segment size of nine pixels. The density of 1,000
used tiles of 512 pixels and a minimum of one pixel, because 1,000 segments per km² in tiles of 1,024 pixels exhausted
memory and a minimum of nine pixels left 20.5 % of the parcel area without segments. The density of 1,000 is therefore
not a comparison in which only the density changed, and the small effect on the P3 status is observed across the tested
segmentation configurations. Since release v1.0.0rc5 `geocrop segmentation-sweep` warns about both situations.
