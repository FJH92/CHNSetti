"""Compare automatic peak boundaries (classical, advanced) and Eager's saved integration
over an archive of Flash 2000 runs, using criteria that do not depend on any analyst's choice.

Usage: python validate_boundaries.py CHNSetti.py ARCHIVE_FOLDER OUT.json [part parts]

Criteria, per element:
  check_error_pp   |result - theoretical composition| of check materials (not in the fit), percentage points
  loo_recovery_err |recovery - 100 %| of each standard when it is left out of the calibration
  replicate_rsd    relative standard deviation of replicate portions of one sample, %
  review_rate      share of peaks whose integration the method itself flags (tail, overlap, weak signal)
  vs_eager_rel     |area / Eager area - 1| (comparison only, not a criterion of correctness)
"""
import sys, os, json, math, re, statistics, importlib.util, traceback
from pathlib import Path

spec = importlib.util.spec_from_file_location('c', sys.argv[1]); C = importlib.util.module_from_spec(spec)
sys.modules['c'] = C; spec.loader.exec_module(C)
ARCHIVE, OUT = sys.argv[2], sys.argv[3]
part, parts = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (0, 1)

MASS = {'C': 12.011, 'H': 1.008, 'N': 14.007, 'O': 15.999, 'S': 32.06}
FORMULA = {'sulphanilamide': 'C6H8N2O2S', 'sulfanilamide': 'C6H8N2O2S', 'sulphanilimide': 'C6H8N2O2S',
           'bbot': 'C26H26N2O2S', 'cystine': 'C6H12N2O4S2', 'methionine': 'C5H11NO2S',
           'acetanilide': 'C8H9NO', 'atropine': 'C17H23NO3', 'sulfanilic': 'C6H7NO3S', 'cysteine': 'C3H7NO2S'}
# flags about the integration itself (not about calibration range or element assignment)
BOUNDARY_FLAGS = {'tail_end_not_resolved', 'tail_continues_beyond_end', 'left_tail_unresolved', 'right_tail_unresolved',
                  'window_edge_boundary', 'overlapping_peaks', 'tail_rises_again', 'weak_signal', 'nonpositive_area',
                  'substantial_negative_contribution', 'trace_edge_boundary', 'tail_model_unavailable', 'truncated_or_unresolved_peak'}
ELEMENT_KEY = {'N': 'N', 'C': 'C', 'H': 'H', 'S': 'S'}


def theory(name):
    key = re.sub(r'[^a-z]', '', (name or '').lower())
    for word, formula in FORMULA.items():
        if word in key:
            counts = {e: int(n or 1) for e, n in re.findall(r'([A-Z][a-z]?)(\d*)', formula)}
            total = sum(MASS[e] * n for e, n in counts.items())
            return {e: 100 * MASS[e] * counts.get(e, 0) / total for e in 'NCHS'}
    return None


def loo(points):
    """Leave-one-out recovery for the averaged response-factor calibration (area / element mass)."""
    use = [p for p in points if p.get('area') and p.get('amount') and p['amount'] > 0 and p['area'] > 0]
    out = []
    for i, p in enumerate(use):
        others = [q['area'] / q['amount'] for j, q in enumerate(use) if j != i]
        if len(others) >= 1:
            out.append(abs(100 * (p['area'] / p['amount']) / statistics.fmean(others) - 100))
    return out


def evaluate(project, preview, basis):
    """basis: 'classical'/'advanced' use the preview's own areas; 'eager' uses Eager's saved areas."""
    out = {e: {'check_error_pp': [], 'loo_recovery_err': [], 'replicate_rsd': [], 'review': [0, 0], 'vs_eager_rel': [],
               'checks': [], 'r_squared': None} for e in 'NCHS'}
    records = {r.index: r for r in project.records}
    for e in 'NCHS':
        cal = preview['calibrations'].get(e) or {}
        pts = []
        for p in cal.get('points') or []:
            if not p.get('included') or not p.get('amount_mg'):
                continue
            item = preview['records'].get(str(p['id']), {}).get('elements', {}).get(e) or {}
            area = item.get('saved_area') if basis == 'eager' else p.get('area')
            pts.append({'area': area, 'amount': p['amount_mg']})
        out[e]['loo_recovery_err'] = loo(pts)
        factors = [p['area'] / p['amount'] for p in pts if p['area'] and p['area'] > 0]
        k = statistics.fmean(factors) if factors else None
        if basis != 'eager':
            out[e]['r_squared'] = cal.get('r_squared')
        groups = {}
        for key, rec in preview['records'].items():
            r = records.get(int(key)); item = rec.get('elements', {}).get(e) or {}
            if r is None or r.role not in ('Sample', 'Check', 'Calibration') or not item:
                continue
            if basis != 'eager' and item.get('area') is not None:
                out[e]['review'][1] += 1
                out[e]['review'][0] += bool(BOUNDARY_FLAGS.intersection(item.get('flags') or []))
                if item.get('saved_area'):
                    out[e]['vs_eager_rel'].append(abs(item['area'] / item['saved_area'] - 1) * 100)
            if r.role == 'Calibration' or not r.weight_mg:
                continue
            area = item.get('saved_area') if basis == 'eager' else item.get('area')
            value = 100 * area / k / r.weight_mg if (k and area is not None) else None
            if value is None:
                continue
            if r.role == 'Check':
                t = theory(r.group or r.name)
                if t and t[e] > 0.05:
                    out[e]['check_error_pp'].append(abs(value - t[e]))
                    out[e]['checks'].append([r.name, round(value, 4), round(t[e], 4)])
            elif r.role == 'Sample':
                groups.setdefault(r.group or r.name, []).append(value)
        for g, values in groups.items():
            if len(values) >= 2 and statistics.fmean(values) > 0.2:
                out[e]['replicate_rsd'].append(100 * statistics.stdev(values) / statistics.fmean(values))
    return out


runs = sorted({str(p) for p in Path(ARCHIVE).rglob('*') if p.suffix.lower() == '.mth'})[part::parts]
result = {}
for run in runs:
    name = Path(run).parent.name
    try:
        project = C.import_file(run)
        entry = {}
        for method in ('classical', 'advanced'):
            settings = C.processing_default_settings(project); settings['boundary_method'] = method
            preview = C.preview_native_processing(project, settings)
            entry[method] = evaluate(project, preview, method)
            if method == 'classical':
                entry['eager'] = evaluate(project, preview, 'eager')
        result[name] = entry
        print('OK', name, flush=True)
    except Exception as exc:
        result[name] = {'error': repr(exc)}; print('ERR', name, exc, flush=True); traceback.print_exc()
Path(OUT).write_text(json.dumps(result), encoding='utf-8')
