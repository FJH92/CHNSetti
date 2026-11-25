# CHNSetti

**Current version:** v1.0.0
**Latest version file:** `src/chnsetti.py`

CHNSetti is an open-source Python desktop application for processing and quality review of CHNS elemental analysis data.

CHNSetti is the third application in a series of open-source tools for laboratory data processing, after [Elementti](https://github.com/FJH92/Elementti) (SEM-EDS elemental maps) and [Plasmatti](https://github.com/FJH92/Plasmatti) (ICP-OES data).

## Citation

An article describing CHNSetti is in preparation. Until it is published, please cite this repository (see `CITATION.md`).

## Overview

CHNSetti processes the data of a Thermo Scientific Flash 2000 Organic Elemental Analyzer (CHNS-O) run with Eager 300 software. Eager 300 writes into one run folder the `.MTH` method and sample table, one `.DAT` file per analysis (detector signal and saved integration), the `.SUM` summary, and further files. CHNSetti opens a method with its detector records, lets the user review the calibration and every chromatogram, and reports the nitrogen, carbon, hydrogen, and sulfur contents of the samples.

Automatic proposals and manual edits of integration boundaries and baselines use the unsmoothed detector signals, and calibration standards and samples use the same numerical integration. The original instrument files and saved results are never modified, and every processing decision, exclusion, revision, and its reason is recorded.

## Main features

* read Eager 300 run folders natively: the `.MTH` method with its `.DAT` detector records (the `.SUM` summary is optional)
* also import Excel (XLS/XLSX) and CSV exports, and select runs from a history ZIP archive
* identify calibration standards, check materials, samples, and bypass runs, and group replicate measurements
* review the calibration of each element against the check material and its certificate, and exclude or restore a standard with one click
* choose between averaged K factor, least-squares through the origin, and fitted-intercept calibration models
* inspect every chromatogram, replay the instrument's saved integration, and propose new baselines and integration intervals
* edit integration intervals and baseline endpoints by dragging on the curve
* compare results with reference values of check materials
* mark values outside the range of the standards
* keep a complete record of processing decisions, reviewed zeros, point exclusions, revisions, and their reasons
* export review and report workbooks, a detailed calculations workbook, a Word report, and a project file
* save the project at any stage and reopen it later
* run from the command line without PySide6
* create a standalone Windows executable
* load built-in synthetic demonstration data

## Repository contents

* `src/chnsetti.py` – the program, as one file
* `requirements.txt` – required Python packages
* `CHANGELOG` – changes in each version
* `CITATION.md` – how to cite CHNSetti
* `LICENSE` – software license
* `README.md` – project description and usage instructions

## Requirements

* Python 3 (tested with Python 3.13)
* PySide6 ≥ 6.5 (only for the desktop application)
* openpyxl ≥ 3.1
* xlrd ≥ 2.0.1 (optional, for some older `.xls` files)

NumPy and SciPy are not needed.

## Installation

1. Install Python 3.
2. Clone or download this repository.
3. Install the required packages:

```bash
pip install -r requirements.txt
```

Alternatively, on Windows:

```bash
py -m pip install PySide6 openpyxl
```

## How to run

Start the desktop application:

```bash
python src/chnsetti.py
```

On Windows, this may also be run with:

```bash
py src/chnsetti.py
```

To check the installation without opening a window, run the built-in demo check:

```bash
python src/chnsetti.py --check-demo
```

## Command line

The command-line interface uses the same calculation engine as the desktop application and does not need PySide6. To see its options:

```bash
python src/chnsetti.py analyze --help
```

For example, to process a run folder and save the outputs:

```bash
python src/chnsetti.py analyze "path/to/run folder" --output results
```

To list the CHNS runs and spreadsheets in a history ZIP archive:

```bash
python src/chnsetti.py list-archive "path/to/archive.zip"
```

## Windows executable

For users who do not want to run the Python source code directly, a Windows executable may be provided as a GitHub release asset. Use the GitHub Releases page to download it when available.

You can also build it yourself on Windows:

```bash
python src/chnsetti.py --make-exe
```

## Demo data

You can try CHNSetti without your own instrument files: the demonstration data are built into the program.

1. Start CHNSetti and click **Start**.
2. In step 1 (**Files**), click **More import options** and choose **Load demonstration data**.
3. Click **Next** through the steps to see the identification, calculation rules, results, and export.

The demonstration contains calibration standards, a check material, bypass runs, and two samples measured in triplicate. It is simulated and does not come from real laboratory measurements. Because it contains no detector traces, the calibration and chromatogram steps (4 and 5) are skipped; use your own Eager 300 run folder to try those steps.

To check the demonstration from the command line instead:

```bash
python src/chnsetti.py --check-demo
```

## Typical workflow

The desktop wizard processes one run in seven steps:

1. **Files:** choose a run folder, a file in an archive, a saved project, or the demonstration data (**More import options → Load demonstration data**).
2. **Identification:** confirm the roles and groups of the measurements.
3. **Calculation rules:** confirm the reporting settings, references, and quality-control thresholds; save or reuse a laboratory preset.
4. **Calibration:** check the calibration curve of each element against the check material and its certificate.
5. **Chromatograms:** check every peak and adjust integrations where needed.
6. **Results:** review the report table.
7. **Generate:** record the source review and export the report package.

Steps 4 and 5 are skipped when the run has no detector traces.

## Output files

Each export creates a new folder containing:

* `CHNS results - review.xlsx` – a workbook for checking the results in the laboratory
* `CHNS results - report.xlsx` – the report for the researcher
* `Detailed calculations.xlsx` – every measurement, calibration, and decision
* `Detailed explanations.docx` – a Word report explaining the calculations
* `Project.CHNSetti.json` – the project file, which can be reopened

## Development

CHNSetti was developed in the High-Temperature Processes and Materials Group at Åbo Akademi University, Turku, Finland.

## Status

Version **v1.0.0** is the first public release.

## Authors

Farzad Jafarihonar, Luis Bezerra, and Emil Vainio
Åbo Akademi University
Turku, Finland

Contact: farzad.jafarihonar@abo.fi

## License

CHNSetti is distributed under the GPL-3.0 license. See `LICENSE` for details.
