"""Compare CHNSetti's pure-Python kernels with NumPy/SciPy (needs numpy+scipy only for this test).
Usage: python test_kernels_vs_scipy.py CHNSetti_1_4_4.py [ARCHIVE_FOLDER]"""
import sys, random, glob, importlib.util, math
import numpy as np
from scipy import signal as sps, sparse
from scipy.sparse.linalg import spsolve
s = importlib.util.spec_from_file_location('c', sys.argv[1]); C = importlib.util.module_from_spec(s); sys.modules['c'] = C; s.loader.exec_module(C)
random.seed(4)
traces = []
if len(sys.argv) > 2:
    for path in sorted(glob.glob(sys.argv[2] + '/**/*.DAT', recursive=True))[::25]:
        try: traces.append([float(v) for v in C.parse_native_dat(open(path, 'rb').read(), path)['signal']])
        except Exception: pass
for _ in range(30):
    n = random.randint(20, 400)
    base = [random.gauss(0, 1) + 50 * math.exp(-((i - n / 2) / (n / 15)) ** 2) for i in range(n)]
    traces.append([round(v) for v in base] if random.random() < .5 else base)
worst = {}
def rel(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    return float(np.max(np.abs(a - b)) / max(1.0, float(np.max(np.abs(b)))))
fails = 0
for t in traces:
    for w in (5, 9, 15):
        if w > len(t): continue
        for order in (1, 2):
            r = rel(C._num_savgol(t, w, order), sps.savgol_filter(np.asarray(t), w, order, mode='interp'))
            worst['savgol'] = max(worst.get('savgol', 0), r)
    sm = C._num_savgol(t, 9, 2) if len(t) >= 9 else t
    noise = max(.5, float(np.std(np.diff(t))))
    for thr in (noise, 3 * noise, 10 * noise):
        p1, pr1 = C._num_find_peaks(sm, height=thr, prominence=thr, width=3.0, plateau=True)
        p2, pr2 = sps.find_peaks(np.asarray(sm), height=thr, prominence=thr, width=3.0, plateau_size=(None, None))
        same = list(p1) == [int(v) for v in p2] and all(rel(pr1[k], pr2[k]) < 1e-12 for k in ('prominences', 'widths', 'plateau_sizes') if len(p2))
        fails += not same
        q1, _ = C._num_find_peaks([-v for v in sm], prominence=thr); q2, _ = sps.find_peaks(-np.asarray(sm), prominence=thr)
        fails += list(q1) != [int(v) for v in q2]
    y = np.asarray(t, float); n = len(y)
    wts = [random.uniform(1e-6, 1) for _ in range(n)]
    D = sparse.diags([np.ones(n - 2), -2 * np.ones(n - 2), np.ones(n - 2)], [0, 1, 2], shape=(n - 2, n), format='csc')
    ref = spsolve(1e6 * (D.T @ D) + sparse.diags(wts, format='csc'), np.asarray(wts) * y)
    worst['whittaker'] = max(worst.get('whittaker', 0), rel(C._num_whittaker_solve(wts, list(y), 1e6), ref))
    if n >= 5:
        k = np.asarray([1., 2., 3., 2., 1.]) / 9.
        worst['reflect_convolve'] = max(worst.get('reflect_convolve', 0), rel(C._num_reflect_convolve5(list(y), list(k)), np.convolve(np.pad(y, (2, 2), mode='reflect'), k, mode='valid')))
    xs = [float(i) for i in range(8)]; ys = [random.gauss(100, 3) for _ in xs]; ww = [random.uniform(.2, 1) for _ in xs]
    A = np.column_stack((np.ones(8), xs)) * np.sqrt(ww)[:, None]
    worst['weighted_line'] = max(worst.get('weighted_line', 0), rel(C._proc_weighted_line(xs, ys, ww), np.linalg.lstsq(A, np.asarray(ys) * np.sqrt(ww), rcond=None)[0]))
print('signals tested:', len(traces))
for k, v in worst.items(): print(f'{k:18s} max relative difference {v:.2e}')
print('find_peaks mismatches:', fails)
ok = fails == 0 and worst['savgol'] < 1e-9 and worst['whittaker'] < 1e-6 and worst['reflect_convolve'] < 1e-12 and worst['weighted_line'] < 1e-9
print('PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)
