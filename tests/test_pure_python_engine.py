"""Compare the processing results of two CHNSetti versions (e.g. 1.4.3 with NumPy/SciPy and
1.4.4 pure Python) for every run in an archive: automatic and instrument-boundary previews.
Usage: python test_pure_python_engine.py OLD.py NEW.py ARCHIVE_FOLDER [baseline_method] [step]"""
import sys, glob, importlib.util, math, time
def load(path, name):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); sys.modules[name] = m; s.loader.exec_module(m); return m
old, new = load(sys.argv[1], 'old'), load(sys.argv[2], 'new')
method = sys.argv[4] if len(sys.argv) > 4 else 'linear'; step = int(sys.argv[5]) if len(sys.argv) > 5 else 1
runs = sorted({p for p in glob.glob(sys.argv[3] + '/**/*', recursive=True) if p.lower().endswith('.mth')})[::step]
import os
# Fields that a newer version adds (listed in NEW_KEYS, comma-separated) are ignored; every shared field is compared.
ADDED = set(filter(None, os.environ.get('NEW_KEYS', '').split(',')))
SKIP = {'content_digest', 'created_utc', 'time_utc', 'engine_version', 'saved_utc'}
# Hash identifiers of calibration content change when any float changes in its last digits; the values themselves are compared.
HASHES = ('calibration_id', '_digest', '_sha256', 'fingerprint')
tol = 1e-9 if method == 'linear' else 1e-6
stats = {'numbers': 0, 'worst': 0.0, 'mismatch': []}
def compare(a, b, path):
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) - SKIP != set(b) - SKIP - ADDED: stats['mismatch'].append((path, 'keys')); return
        for k in a:
            if k in SKIP or any(h in str(k) for h in HASHES): continue
            compare(a[k], b[k], path + '/' + str(k))
    elif isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b): stats['mismatch'].append((path, 'length', len(a), len(b))); return
        for i, (x, y) in enumerate(zip(a, b)): compare(x, y, path + f'[{i}]')
    elif isinstance(a, float) or isinstance(b, float):
        if isinstance(a, bool) or isinstance(b, bool) or not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            if a != b: stats['mismatch'].append((path, a, b)); return
            return
        stats['numbers'] += 1
        if math.isnan(a) and math.isnan(b): return
        d = abs(a - b) / max(1.0, abs(a))
        stats['worst'] = max(stats['worst'], d)
        if d > tol: stats['mismatch'].append((path, a, b))
    elif a != b:
        stats['mismatch'].append((path, a, b))
times = [0.0, 0.0]
for run in runs:
    po, pn = old.import_file(run), new.import_file(run)
    for fn in ('preview_native_processing', 'processing_saved_preview'):
        so = old.processing_default_settings(po); sn = new.processing_default_settings(pn)
        so['baseline_method'] = method; sn['baseline_method'] = method
        t = time.time(); a = getattr(old, fn)(po, so); times[0] += time.time() - t
        t = time.time(); b = getattr(new, fn)(pn, sn); times[1] += time.time() - t
        compare(a, b, run.split('/')[-2] + ':' + fn)
print(f'runs {len(runs)} | baseline {method} | numbers compared {stats["numbers"]} | worst relative difference {stats["worst"]:.2e} | mismatches {len(stats["mismatch"])}')
print(f'time NumPy/SciPy {times[0]:.1f} s | pure Python {times[1]:.1f} s')
import collections
kinds = collections.Counter(m[0].split('/')[-1].split('[')[0] for m in stats['mismatch'])
print('mismatch fields:', dict(kinds.most_common(10)))
structural = [m for m in stats['mismatch'] if not (len(m) == 3 and isinstance(m[1], float) and isinstance(m[2], float))]
print('structural mismatches (boundaries, flags, statuses, counts):', len(structural))
for m in structural[:5]: print('  !', m)
for m in stats['mismatch'][:10]: print('  ', m)
sys.exit(0 if not stats['mismatch'] else 1)
