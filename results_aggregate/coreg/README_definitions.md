# Definitions in the co-registration tables

- `coreg_before_after_E0_E8.csv`: main five-fold 5 km spatial block partition (244 polygons, 5044 pixels). `*_macro_f1` is the mean F1 over all nine classes. `*_macro_f1_soybean_sunflower` is the mean F1 of soybean and sunflower only (the target classes of the engine configuration used for these experiments); it is **not** the three-class measure of the paper.
- `coreg_paired_by_partition.csv`, `coreg_paired_summary.csv`: twelve spatial block partitions (3, 5 and 8 km, four shifted origins each). `macro_F1_maize_soybean_sunflower` is the mean F1 of maize, soybean and sunflower (the three-class measure used in the paper's text and Table S6).
