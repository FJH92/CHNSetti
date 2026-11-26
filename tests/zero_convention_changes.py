"""Every report cell that differs between two versions, classified (for the 0-instead-of-NQ change).
Usage: python zero_convention_changes.py OLD.py NEW.py ARCHIVE

Expected kinds: a portion cell "Missing" → 0, and avg./stdev. cells of the same group and element.
Anything else is listed as UNEXPECTED."""
import sys, re, tempfile, importlib.util, collections
from pathlib import Path
from openpyxl import load_workbook
def load(p, n):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m
old, new = load(sys.argv[1], 'old'), load(sys.argv[2], 'new')
runs = sorted({str(p) for p in Path(sys.argv[3]).rglob('*') if p.suffix.lower() == '.mth'})
kinds = collections.Counter(); unexpected = []; runs_changed = 0
for run in runs:
    sheets = []
    for m in (old, new):
        p = m.import_file(run); m.set_settings(p, expected_replicates=3)
        path = m.export_analysis(p, tempfile.mkdtemp())['CHNS results - report']
        ws = load_workbook(path, data_only=True).worksheets[0]
        sheets.append([list(r) for r in ws.iter_rows(values_only=True)])
    a, b = sheets
    if len(a) != len(b):
        unexpected.append((Path(run).parent.name, 'row count', len(a), len(b))); continue
    zero_columns = set(); changed = False
    group_rows = []  # rows of the current block
    for i, (ra, rb) in enumerate(zip(a, b)):
        for j, (x, y) in enumerate(zip(ra, rb)):
            if x == y or (isinstance(x, str) and isinstance(y, str) and re.sub(r'\d+\.\d+\.\d+', 'v', x) == re.sub(r'\d+\.\d+\.\d+', 'v', y)):
                continue
            changed = True
            label = ra[3] if len(ra) > 3 else None
            if x == 'Missing' and y == 0:
                kinds['portion Missing → 0'] += 1; zero_columns.add((len(group_rows), j))
            elif label in ('avg.', 'stdev.') and (x is None or isinstance(x, (int, float))) and isinstance(y, (int, float)):
                kinds[f'{label} recalculated with the zeros'] += 1
            else:
                unexpected.append((Path(run).parent.name, i, j, x, y))
        group_rows.append(i)
    runs_changed += changed
print(len(runs), 'runs,', runs_changed, 'with changes')
for k, v in kinds.most_common(): print(f'  {v:5d}  {k}')
print('UNEXPECTED:', len(unexpected))
for u in unexpected[:20]: print('  ', u)
