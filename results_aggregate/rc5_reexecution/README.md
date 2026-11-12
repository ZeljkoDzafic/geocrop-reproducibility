# Re-execution of the main experiments from the tagged release v1.0.0rc5

The stages samples, train and experiments of the 2023 Lijevče polje run were re-executed from a clean checkout of the tag v1.0.0rc5
(commit 7ade928d823cc8a331d4cc2954c2d95610f0c903, Zenodo DOI 10.5281/zenodo.24156741) with the same configuration as the earlier
clean re-execution (, output directory changed only). The earlier run used commit 1f4509036b.

Result (internal cross-validation; not independent accuracy):
- sample file : SHA-256 , identical to the earlier run (5,044 samples, 244 polygons);
- training stage: cross-validation overall accuracy 0.9573750991276765 and macro-F1 0.9474069641738788, identical;
- experiments: all nine rows of  are identical to the earlier run in every numeric column (maximum absolute difference 0).
  The rows E5 and E6 are produced by the engine but are not evaluated in the paper;
- three of the eight output files of the training stage are not byte-identical between the two runs (not investigated), so identity is claimed
  for the metrics and the sample file only.

Command (paths are placeholders; run from a clean worktree of the tag):



Run times are not reported: the machine was not dedicated and the load was not controlled.
