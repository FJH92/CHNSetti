# Automatic start and end points — methods and how to evaluate them on your own archive (CHNSetti 1.0.0)

## The two methods

**Classical** (the original method of the development builds, unchanged): the signal is lightly smoothed (Savitzky–Golay); a peak ends where the smoothed signal falls below 1 % of the peak height or 2.5 × noise for three points in a row; the search stays inside the element's retention window derived from the standards; the baseline is a robust (Huber) straight line through five flank points on each side.

**Advanced** (new, default):

1. **Identification.** A peak is taken as the element only if its apex lies within the method's identification window (stored in the `.MTH`, e.g. ±10 s N, ±15 s C, ±50 s H and S) around the apices of this run's standards. Seconds are converted to detector points with the median pairwise slope (Theil–Sen) between the stored retention times and the standards' apices. Otherwise the element has *no peak at its retention time* — never a zero.
2. **Start and end from the slope of the signal, with noise-adaptive thresholds.** The first derivative is estimated by local least squares (Savitzky–Golay, window adapted to the peak width). A boundary is where the signal is back within 2.5 × the trace's noise of the baseline *and* its slope has stayed within 3 × the slope noise for several points. The baseline is refitted at the new boundaries until they no longer move.
3. **Tails are followed, never into a neighbour.** A slow tail (typically hydrogen) is followed until it really meets the baseline, also past the standards' window, but only while it is still clearly falling; a peak that elutes earlier than in the standards is followed back to where its rise begins. Where a following peak starts first, the boundary is the lowest point between the two.
4. **Baseline points stay in the element's own region.** The flank points of the baseline line may not lie in a neighbouring element's region and stop where the signal rises into the next peak. (The classical method can take points on the steep carbon rise as nitrogen baseline when a large carbon peak follows nitrogen closely, as with BBOT.)
5. **Tail model.** An exponential decay with a straight baseline, y = c0 + c1·t + A·e^(−t/τ), is fitted (robustly) from 10 % of the peak height to the end. If it estimates that more than 1 % of the area lies beyond the end, the peak is flagged.
6. **Same rule for standards and samples**, so systematic tail effects largely cancel through the calibration.

Manual edits are unaffected: a dragged Start or End point always uses the straight baseline from point to point on the trace.

## Criteria

Only criteria that do not depend on an analyst's choice decide; agreement with the instrument's saved integration is
shown for comparison only.

| criterion | meaning |
|---|---|
| **Standards, leave-one-out** | each standard is left out of the K factor of its run and recovered from the others: \|recovery − 100 %\| |
| **Check materials** | BBOT or sulfanilamide measured as a check, against its theoretical composition (formula): \|result − theory\| in percentage points |
| **Replicates** | relative standard deviation of the portions of one sample, % |
| **Flagged** | share of peaks whose integration the method itself flags (tail, overlap, weak signal, …) — work for the analyst |
| **vs Eager** | \|area / Eager's saved area − 1\|, median % (comparison only) |

All standards are included as stored (no exclusions), with the averaged-K calibration of each run. "Eager" is the
integration saved with the run (Eager's automatic one, or the analyst's where it was revised).

## Evaluating on your own archive

```
python tests/validate_boundaries.py src/chnsetti.py ARCHIVE validation.json
python tests/summarize_validation.py validation.json
```

`ARCHIVE` is a folder or ZIP with run folders (`.MTH` with its `.DAT` files). The summary gives, for each element and
for Eager, the classical and the advanced method, the medians (and 90th percentiles) of the criteria above. The
development of CHNSetti used several years of archived routine runs of the authors' laboratory; those data and
their figures are not published.

## Limits

- The check materials are the standards' substances measured as unknowns; their theoretical composition from the
  formula is used, not certificate values.
- With three standards per run, the leave-one-out recovery is coarse.
- These are retrospective comparisons on archived data, not a formal method validation (no independent reference
  materials beyond the checks, no inter-laboratory comparison).
- Both methods are proposals: nothing enters the report until it is applied and recorded. The classical method gives
  the same proposals as in the development builds.
