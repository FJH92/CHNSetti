"""The classical automatic method of NEW gives exactly the proposals of OLD (boundaries, areas, values, flags).
Usage: python classical_unchanged.py OLD.py NEW.py ARCHIVE"""
import sys, importlib.util, json
from pathlib import Path
def load(p, n):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m
old, new = load(sys.argv[1], 'old'), load(sys.argv[2], 'new')
runs = sorted({str(p) for p in Path(sys.argv[3]).rglob('*') if p.suffix.lower() == '.mth'})
bad = 0; n = 0
for run in runs:
    po, pn = old.import_file(run), new.import_file(run)
    a = old.preview_native_processing(po, old.processing_default_settings(po))
    st = new.processing_default_settings(pn); st['boundary_method'] = 'classical'
    b = new.preview_native_processing(pn, st)
    for k, rec in a['records'].items():
        for e, x in rec['elements'].items():
            y = b['records'][k]['elements'][e]; n += 1
            for key in ('start', 'end', 'area', 'value', 'status'):
                if x.get(key) != y.get(key):
                    bad += 1; print('DIFF', Path(run).parent.name, k, e, key, x.get(key), y.get(key)); break
    for e in a['calibrations']:
        if a['calibrations'][e].get('slope') != b['calibrations'][e].get('slope'):
            bad += 1; print('DIFF calibration', Path(run).parent.name, e)
print(len(runs), 'runs', n, 'peaks compared', bad, 'differences')
