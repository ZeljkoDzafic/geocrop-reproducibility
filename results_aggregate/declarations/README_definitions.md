# Definitions in the declaration tables

- Unit of analysis: the declaration (one row per declared parcel). Areas are sums over declarations; a physical area covered by overlapping declarations counts once per declaration.
- `data_check.csv`, `declarations_with_no_pixel_centre = 25`: declarations whose geometry contains no 10 m pixel centre of the probability grid (computed directly on the E8 grid with the same rule used by `geocrop crop-presence`). An earlier version of this table gave 116; that number came from a global rasterisation in which overlapping declarations hid each other's pixels ("last declaration wins") and was wrong for this criterion. Table S10 of the paper therefore covers 4,973 declarations (4,998 - 25).
- `declarations_below_95pct_inside_aoi = 2` (AOI-containment criterion) and `declarations_below_95pct_valid_pixels = 1` (valid-pixel coverage criterion) are different criteria; `partly_outside_aoi_flag = 3` is their union.
