# CHNSetti synthetic demonstration run

**All signals, names, masses and compositions in these files are invented. They contain no laboratory measurements.**
The `.MTH` and `.DAT` files cover only the fields CHNSetti reads; they are not instrument files and must not be opened
in Eager 300 or used on an analyzer.

The files are written by CHNSetti itself (`py src/chnsetti.py --write-demo FOLDER`, or step 1 → More import options →
Demonstration), always byte for byte the same; the copies here are for looking at without running the program.

- `SYNTHETIC_main/` — 15 measurements: 2 bypass runs, 3 standards (Demo Std A, B, C), BBOT as the check material and
  three samples (Demo A, B, C) in three portions each.
- `SYNTHETIC_file_repair/` — the same run with the contents of `SYN006.DAT` and `SYN007.DAT` exchanged.
- `synthetic_manifest.json` — the simulated composition of every measurement, the saved integrations and the built-in
  problems.

The check material is compared with the composition of BBOT (C26H26N2O2S) calculated from its formula:
N 6.51, C 72.53, H 6.09, S 7.45 % w/w. This is not a certificate.

## Built-in problems and what CHNSetti 1.0.0 does with them (default settings, no corrections)

| Problem | Result |
|---|---|
| Nitrogen response of Demo Std B 45 % too high | Demo Std B left out for nitrogen only; check material N 5.65 → 6.49 % (formula 6.51 %) |
| Hydrogen tail of Demo A - 1 cut off in the saved integration (end at point 853) | End point 952; area +15 %; H 4.32 → 5.00 % (simulated 5.0 %) |
| Clear sulfur peak of Demo A - 2 missing from the saved integration | Reported, 4.10 % S (simulated 4.1 %), marked for a look |
| No sulfur signal in Demo A - 3 | Only this sulfur left out of the mean (Demo A: n = 3, 3, 3, 2) |
| Demo B - 3 at 3.5 % of the normal signal | Whole portion left out (Demo B: n = 2) |
| No sulfur in Demo C | 0 in all three portions, counted |
| File repair: two data files swapped | Both found in step 2; the right files proposed and linked on confirmation |

Every mean differs from the simulated composition by less than 0.03 percentage points. The new sulfur peak of Demo A - 2
is marked for a look in step 5; step 7 asks to check the two failed portions and to sign off. This shows that the rules behave as intended on known problems; it is not a
measure of the accuracy of CHNS analysis.

Test: `tests/test_full_demo_100.py` repeats all of the above through the production engine.
