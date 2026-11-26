"""Which advanced proposals differ between two versions. Usage: python advanced_changes.py OLD.py NEW.py ARCHIVE"""
import sys, importlib.util
from pathlib import Path
def load(p, n):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m
old, new = load(sys.argv[1], 'old'), load(sys.argv[2], 'new')
runs = sorted({str(p) for p in Path(sys.argv[3]).rglob('*') if p.suffix.lower() == '.mth'})
n = changed = 0
for run in runs:
    po, pn = old.import_file(run), new.import_file(run)
    a = old.preview_native_processing(po, old.processing_default_settings(po)); b = new.preview_native_processing(pn, new.processing_default_settings(pn))
    for k, rec in a['records'].items():
        for e, x in rec['elements'].items():
            y = b['records'][k]['elements'][e]; n += 1
            if any(x.get(f) != y.get(f) for f in ('start', 'end', 'area', 'value', 'status')):
                changed += 1
                print('CHANGED', Path(run).parent.name, k, e, (x.get('start'), x.get('end'), x.get('area')), '->', (y.get('start'), y.get('end'), y.get('area')))
print(len(runs), 'runs', n, 'advanced peaks compared', changed, 'changed')
