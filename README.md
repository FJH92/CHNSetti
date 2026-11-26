# CHNSetti 1.0.0

CHNS elemental-analysis processing for the **Thermo Scientific Flash 2000 Organic Elemental Analyzer (CHNS-O)** with **Eager 300** software.
Laboratory of High Temperature Processes and Materials, Åbo Akademi University. Licence: GPL-3.0 (see `LICENSE`).

CHNSetti is the third application in a series of open-source tools for laboratory data processing, after [Elementti](https://github.com/FJH92/Elementti) (SEM-EDS elemental maps) and [Plasmatti](https://github.com/FJH92/Plasmatti) (ICP-OES data).

## Run from source

```
py -m pip install PySide6 openpyxl
py src/chnsetti.py
```

Command line (no window): `py src/chnsetti.py analyze RUN.MTH -o OUTPUT_FOLDER` exports the instrument's results; add `--process-native` to process the run as the wizard does (CHNSetti's integration, the default choice of standards, the small-peak rule and the failed-portion rule; the same report as the wizard with the same settings), and `--all-standards` to keep every standard. Self-check: `py src/chnsetti.py --check-demo`.

## Try it without laboratory data

Step 1 → **More import options → Demonstration (synthetic data)**:

- **Full run with detector signals** — a synthetic run (one `.MTH`, 15 `.DAT` files) written by CHNSetti itself and opened
  through the ordinary import, so all seven steps can be tried. Invented signals, names, masses and compositions; the
  window title, the step list and every exported file say *SYNTHETIC DEMONSTRATION*. Problems built in: a standard
  reading 45 % high in nitrogen (left out by the default choice), a hydrogen tail cut off in the saved integration, a
  clear sulfur peak missing from the saved integration, a portion without sulfur, a portion that did not burn, and a
  sample without sulfur (reported as 0). The check material (BBOT) is compared with its composition calculated from
  the formula, kept with the demonstration project only.
- **File repair: two data files swapped** — the same run with the contents of two data files exchanged; step 2 finds
  both and proposes the right files.
- **Results table only** — the earlier small demonstration without detector signals.

The files are written to a folder of their own in the temporary folder (`CHNSetti full demonstration`), never next to
real runs; `py src/chnsetti.py --write-demo FOLDER` writes them anywhere. The same files and a description of the
built-in problems are in `demo/`. These files are not instrument files: do not open them in Eager 300.

## Requirements

**CHNSetti.exe** needs nothing installed. The `.py` file needs only Python 3.10+ with **PySide6** and **openpyxl**, the same kind of setup as Elementti and Plasmatti. CHNSetti does not use NumPy or SciPy: the chromatogram processing (baselines, peak finding, integration, calibration) is written in plain Python.

## Build CHNSetti.exe (Windows)

Double-click `build_windows.bat`, or run `py src/chnsetti.py --make-exe`. The logo and icon are embedded in the source file.

## What the export contains

Five files, as before: `CHNS results - report.xlsx` (the historical report format), `CHNS results - review.xlsx`, `Detailed calculations.xlsx`, `Detailed explanations.docx` and `Project.CHNSetti.json`.

- **0, not NQ.** An element without a peak — none in the instrument's saved integration and, when CHNSetti's integration is applied, none there either — is reported as **0** and counted in the average and standard deviation, as in the laboratory's historical reports. "NQ" and "Missing" are not written in the report. The audit still records such a value as *not quantified* (a reporting convention, not a measurement). If only one of the two integrations found a peak, the value waits for the analyst's decision.
- **`Detailed explanations.docx`** is written to be read from top to bottom: status (reviewed or not, with the number of open points), **1. Summary**, **2. Results** (mean ± SD per sample, then the individual portions), **3. Calibration** (the factor K of each element in *peak area = K × element mass*, standards used, recoveries, excluded standards with reasons, recovery of each standard, the calibration curves), **4. Changes made by the analyst** (in plain sentences), **5. How the results were calculated**, **6. Open points**, **7. Chromatograms** (one figure per standard, check material and sample, each element's integrated area shaded), and an **appendix** with the source files and their SHA-256 fingerprints. The figures show the integration behind the report: CHNSetti's applied integration when applied, otherwise the instrument's saved integration.

## Which files are needed

Select only the `.MTH` file; keep the whole run folder together. Eager 300 writes all of these into the run folder:

| File | Contents | Used by CHNSetti |
|---|---|---|
| `.MTH` | Method, sample table, masses, element identification table (retention time and window per element) | Yes — the entry point |
| `.DAT` (one per analysis) | Detector signal plus the saved peak integration; written when each analysis ends (about every 12 min) | Yes — chromatograms, automatic integration, instrument values |
| `.SUM` | Summary of the saved percentages | Optional import/comparison |
| `cc.cc` | Eager's CFR21_11 log: when each file was last saved | Yes — shows which measurements were re-integrated in Eager after the run |
| `.EAM` | Instrument parameters | Not used |

When the analyst re-integrates in Eager 300 and saves, the `.DAT` files, `.MTH`, `.SUM` and `cc.cc` are overwritten in place (the detector signals stay the same). **Keep a copy of the run folder as the instrument left it** (before reviewing in Eager) if you want the original instrument processing on record.

## Workflow

1. **Files**: open the `.MTH` file of the run.
2. **Identification**: check the Role and Group of each measurement. Clicking a row shows its chromatogram (the instrument's peaks, read-only) under the table, with the name of its data file, so an empty capsule or a mislabelled bypass shows at once.
   - **More** holds *Suggest groups…*, *Group selected rows…* and *Exclude selected rows from the statistics…*.
   - **Data files…** lists every row of the sequence with the file it reads and what is *inside* that file (sample name, mass, time of measurement). Rows without a usable file are orange, and an orange bar above the table names them. **Click a data file** to change it: the list offers CHNSetti's suggestion first (the file whose own name and mass match the row), then the free files of the run folder with what is inside each, *Choose a file…*, *Not measured / lost* and *No file for this row*. **Double-click a name or mass** to correct a typing error. **Use all suggestions** fixes every orange row at once. Changes are saved at once and recorded with the computer login, the time and what the row was before; a note is optional. The MTH name, mass and file identifier stay in the record. A file whose own name and mass differ from the row is used only after confirming; a file already used by another row cannot be chosen. In the file-repair demonstration, the contents of two data files are swapped; **Use all suggestions** links each row to the file whose contents match.
3. **Calculation rules**: one Settings card (run name, requester, portions, RSD flag, whether the check material goes into the report, notes; **Presets** is one menu to use, save, rename, delete, export or import laboratory presets) and **Peak start and end**: **Advanced** (default) or **Classical** (the method of 1.4.0–1.4.8, unchanged) for the automatic integration. See `VALIDATION.md`.
4. **Calibration**: the curves, checked against the check material and its certificate. It comes before the chromatograms: the calibration is settled first, as in the laboratory's practice.
   - **Nitrogen / Carbon / Hydrogen / Sulfur** buttons choose the curve. It shows the standards and the fitted line; the box on it says, in words: *Nitrogen: peak area = K × nitrogen mass / K = 3.006 × 10⁶ per mg / 2 standards · recoveries 99.8 – 100.2 %* (synthetic demonstration). R² is in the box's tooltip (with three standards on a line through the origin it is almost always above 0.99; the recoveries say more). Axes: *carbon in the portion (mg)* and *peak area*. Zoom with the wheel or **+ / −**, **0** resets.
   - The list gives each standard's **recovery** with the current curve (its result ÷ its composition); check materials follow with their result and appear on the curve as a yellow diamond when selected.
   - **Click a standard on the curve to exclude it, click again to restore it.** The curve, the recoveries and every result follow at once. Standards without a peak sit on the bottom axis and can be excluded the same way. Points are never removed automatically; the reason given at *Apply to report* is recorded for each excluded standard.
   - **Default choice of standards**: for each element CHNSetti tries every choice that keeps at least two standards and starts from the one that brings the check material closest to its certificate — only if that result is within ±10 % of the certificate and at least a quarter closer than with all standards; otherwise all standards are kept. The check material is whatever the run has (BBOT, sulfanilamide, cystine or methionine). Such a standard is marked *excluded automatically* on the curve and its reason is recorded (*Chosen automatically: brings BBOT closest to its certificate (…)*); click it to restore it, or exclude further by hand, down to one standard. Synthetic demonstration: Demo Std B is left out for nitrogen (BBOT 5.65 → 6.49 % against 6.51 %); the other elements keep all three standards.
   - **Check material against its certificate**: a second box on the curve shows just two numbers for the element: the check material's result with the current curve and its certified value, e.g. *BBOT: 6.49 %   certificate 6.51 %*. It changes at once when a standard is excluded or restored.
   - The axes start at 0 and carry round numbers (0, 0.2, 0.4 mg; 1 000 000, 2 000 000).
   - **Certified values** (above the curve, and only here): the batch of standards the check material is compared with. The two bottle labels are built in (BN 319393, 04.12.2018 and BN 445356, 13.05.2024); the batch dated on or before the run is proposed. **Edit…** shows the values and **New batch…** adds a batch from its label (number, date, values; empty = not certified). A new batch is kept on the computer for later runs and saved in the project file. The built-in label values are read-only. The batch is a comparison only: the calibration uses the composition stored in the method (.MTH), and no reported number depends on the batch.
   - Before excluding a standard, look at its peak: select it and press **See peak** — step 5 opens at that peak; **Back** brings you back.
5. **Chromatograms**: every peak of the run, standards first, then check material and samples, with the calibration of step 4. Only the integration — no curve here.
   - The list shows each element's **result in % w/w** (mass of the element per mass of the weighed portion) with the current calibration; hover a value for its peak area. Orange: needs a look (hover for why — a tail that continues, overlapping peaks, a weak signal, a new element assignment). Red: the instrument integrated a peak that the automatic integration did not find. **Only peaks that need a look** hides the rest.
   - Click a value: the chromatogram opens, zoomed to that peak. **Drag the round marker at the start or the end of the peak**; it slides along the curve and can be placed **anywhere, also between two detector points** (0.01 point). The baseline is drawn straight from the start point to the end point; the area changes smoothly and the point stays where it is released. Afterwards **← / →** move it by one detector point (**Shift**: ten, **Ctrl**: a tenth).
   - The label on the peak shows the result (*H 5.00 % w/w*) and, smaller, the **peak area** in detector units (*area 2.15 × 10⁵*). Both change while you drag.
   - **Left-drag on empty space** moves the view; the **wheel** zooms in time (down to 12 points), **Shift + wheel** the signal axis; double-click or **Full trace** resets.
   - **Keyboard, no wheel or middle button needed**: click the plot, then **+ / −** zoom in time (around the selected peak), **↑ / ↓** zoom the signal axis, **0** shows everything. A mouse with only two buttons can do everything: the middle button only offers an extra drag-to-zoom. In the full trace the small points of the other peaks can be dragged too, and clicking a peak selects it.
   - **No peak found?** Press **Draw peak**, then drag across the trace. **Confirm peak** and **Report as zero…** appear when they apply. Under the plot, in words: *Hydrogen in this portion: 5.00 % w/w · peak area 2.15 × 10⁵ (detector units)*; for a standard, *Carbon found: 34.99 % w/w · known composition 35.0000 % (recovery 100.0 %)*.
   - More → **Advanced chromatogram editor** (baseline methods, exact point indices, instrument boundaries, saved-DAT comparison).
6. **Results**: the report table, full width.
   - **By default the report uses CHNSetti's integration and calibration from steps 4–5** — what you see there is what is reported (green bar). It is recorded once, with the reviewer and the reason *CHNSetti integration and calibration as checked in steps 4–5 (default)*; the instrument's values stay in the project. Where the instrument found no peak, a peak CHNSetti finds is reported only when it is clear (signal-to-noise at least 10, no competing or overlapping peak, apex at the standards' retention); a weaker or uncertain one stays 0, as with the instrument, until you confirm it in step 5. Where neither found a peak, the element is 0 (laboratory convention). **Use the instrument's results instead** in the bar switches this run back; **Apply to report…** puts CHNSetti's results in again.
   - **Failed portions are left out of the mean, not counted as 0**: a portion in which almost nothing burned (N + C + H + S below 10 % of another portion of the same sample), or an element missing in one portion that every other portion contains at 0.5 % or more. The cell reads *Failed*, the result says which portion was left out and why, and with only one usable portion it says so (no standard deviation; consider measuring again). A missing file is not a failed portion. When the portions disagree otherwise (an element in only one of three portions), nothing is left out and the result says to check the chromatograms. A person's decision on a value in Review measurements prevails.
   - A bar above it says whether steps 4–5 are in the report, and how many values would change.
   - **Orange numbers** lie outside the range of the standards (extrapolated); hover for the amounts.
   - **Show peak** opens the selected value's chromatogram in step 5 (on an avg. or stdev. row it lists the portions to choose from; from a name or mass cell it opens the first element with a peak); **How calculated…** (or double-click) explains a number; the summary at the top opens the questions; **More** has group details and the review tools.
   - Steps 4 and 5 are skipped (shown as *not needed*) for a run without detector traces.
7. **Generate**: what still needs a decision, in plain words; **click a name** to open that peak in step 5. **Sign off as final** (one click; the computer login, the time and an optional note are recorded), then **Export** the five standard files.

**Nobody types a reviewer name.** Every recorded decision (applying, excluding, grouping, linking a file, signing off) is saved with the computer login and the time; a note is optional everywhere.

**Please wait.** When a calculation takes more than 2 seconds (the first integration of a run in step 4, the results in step 6, the export), a small box says what CHNSetti is doing, and the window keeps drawing.

**On screen** percentages have four decimals and zero is a plain 0; the exported files keep every digit.

Steps 4, 5 and 6 share one editor: edits and **↶ / ↷** (Ctrl+Z / Ctrl+Y) carry over in every direction.

Save project (Ctrl+S) at any time; unfinished chromatogram edits are saved with the project. Original instrument files are never modified.

## Tests

The tests below run on the synthetic demonstration (`py src/chnsetti.py --write-demo demo` writes it; the copy in
`demo/` is the same) or on a run of your own. `DEMO` stands for `demo/SYNTHETIC_main/SYNTHETIC_CHNS.MTH`.

- `tests/test_full_demo_100.py src/chnsetti.py [RUN.MTH]`: the full demonstration through the production engine — files identical each time, roles and groups, standard B left out for nitrogen only, the hydrogen tail recovered to the simulated 5.0 %, the missed sulfur peak reported, both failure rules, zeros kept, no automatic sign-off, file repair, SYNTHETIC in every export, the demonstration recognized however it is opened, reopening; with a run of your own, that its reference is never used for a real run.
- `tests/test_full_demo_gui_100.py src/chnsetti.py`: the three demonstrations from the menu of step 1, the labels, steps 1–7.
- `tests/test_160.py src/chnsetti.py DEMO`: steps 4–6 (calibration, chromatograms, results), See peak / Show peak, Apply in step 6, the method choice, skipping steps 4–5 without traces.
- `tests/test_149.py src/chnsetti.py DEMO`: boundaries between detector points (engine, save, apply, export), switching the automatic method, the calibration equation.
- `tests/test_calibration_and_new_peak.py src/chnsetti.py DEMO`: one-click exclusion/restoration of standards, unblocking a curve, drawing a missing peak, reasons recorded at apply.
- `tests/test_clicks_100.py src/chnsetti.py DEMO`: what a click does — the step 2 chromatogram, no step change on a double-click in step 4, the portion choice of Show peak in step 6, the click hints in the tooltips.
- `tests/test_display_100.py src/chnsetti.py DEMO`: round markers, labels in % w/w, the peak area as a power of ten, the calibration box in words, keyboard zoom in steps 4 and 5, the check-material box and the batch chooser.
- `tests/test_cli_100.py src/chnsetti.py DEMO`: the command line with `--process-native` writes the same report as the wizard; without it, the instrument's results; `--all-standards`.
- `tests/smoke_gui_runs.py src/chnsetti.py demo RUN.MTH …`: every result, every trace, dialogs, apply and export (`demo` = the results-only demonstration).

Tools for comparing versions or methods over an archive of your own runs: `tests/test_kernels_vs_scipy.py`
(the plain-Python numerical routines against SciPy; needs NumPy/SciPy for the comparison only),
`tests/test_pure_python_engine.py`, `tests/regression_compare.py`, `tests/advanced_changes.py`,
`tests/classical_unchanged.py`, `tests/zero_convention_changes.py`, and `tests/validate_boundaries.py` with
`tests/summarize_validation.py` (see `VALIDATION.md`). Further tests used during development run on the authors'
laboratory data and are not published.

These are software tests. They do not establish the analytical validity of the automatic integration.

## Citation

An article describing CHNSetti is in preparation. Until it is published, please cite the software repository (see `CITATION.md`):

Jafarihonar, F., Bezerra, L., & Vainio, E. CHNSetti: Processing and quality review of CHNS elemental analysis data. Version 1.0.0, 2026. https://github.com/FJH92/CHNSetti

## Authors

Farzad Jafarihonar, Luis Bezerra, and Emil Vainio
High-Temperature Processes and Materials Group, Åbo Akademi University, Turku, Finland

Contact: farzad.jafarihonar@abo.fi
