"""Full synthetic demonstration: run through the production engine (native import, choice of standards,
integration, default report, failure rules, file repair, export, reopen).
Usage: python test_full_demo_100.py src/chnsetti.py [real_run.mth]
Based on the 19 checks of the demonstration package, plus labelling and isolation checks."""
import sys, os, math, json, zipfile, tempfile, hashlib, importlib.util, traceback
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
spec = importlib.util.spec_from_file_location('c', sys.argv[1]); m = importlib.util.module_from_spec(spec)
sys.modules['c'] = m; spec.loader.exec_module(m)
REAL = sys.argv[2] if len(sys.argv) > 2 else None
ok = bad = 0


def check(cond, text):
    global ok, bad
    if cond: ok += 1; print('PASS', text)
    else: bad += 1; print('FAIL', text)


def hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(root).rglob('*') if p.is_file()}


try:
    tmp = Path(tempfile.mkdtemp(prefix='chnsetti_demo_'))
    folder = tmp / 'demo'
    m.write_demo_files(folder)
    first = hashes(folder); m.write_demo_files(folder)
    check(hashes(folder) == first, 'demonstration files are identical each time they are written')
    p = m.full_demo_project(folder)
    check(p.demo and p.input_warnings[0] == m.DEMO_WARNING, 'project marked as synthetic, warning first')
    check(len(p.records) == 15 and all(r.dat_info.get('status') == 'verified' for r in p.records), '15 native DAT records read and identity checked')
    check(sum(r.role == 'Sample' for r in p.records) == 9 and len({r.group for r in p.records if r.role == 'Sample'}) == 3, '9 portions grouped into 3 samples')
    check(sum(r.role == 'Calibration' for r in p.records) == 3 and sum(r.role == 'Check' for r in p.records) == 1, '3 standards and 1 check identified')
    check(p.settings.reference_table == m.DEMO_REFERENCE_NAME, 'check material compared with the theoretical composition of BBOT')
    m.apply_edits(p, [{'index': r.index, 'role': r.role, 'group': r.group} for r in p.records])
    original = m.preview_native_processing(p)
    selected, choices = m.auto_select_standards(p, original)
    check([(c['element'], c['excluded']) for c in choices] == [('N', ['Demo Std B'])], 'only nitrogen standard B left out by the default choice')
    n0 = m.check_material_results(p, original, 'N')[0]['found']; n1 = m.check_material_results(p, selected, 'N')[0]['found']
    check(abs(n1 - 6.51) < abs(n0 - 6.51) and abs(n1 - 6.51) < 0.1, f'check N {n0:.3f} -> {n1:.3f} % (formula 6.51 %)')
    item = lambda v, i, e: v['records'][str(i)]['elements'][e]
    h = item(selected, 6, 'H')
    check(h['end'] > h['saved_end'] and h['area'] > h['saved_area'] * 1.10, f"hydrogen tail of Demo A - 1: end {h['saved_end']} -> {h['end']}, area +{100*(h['area']/h['saved_area']-1):.0f} %")
    check(abs(h['value'] - 5.0) < 0.1, f"Demo A - 1 H {h['saved_percent']:.3f} -> {h['value']:.3f} % (simulated 5.0 %)")
    flags = [f for r in selected['records'].values() for it in r['elements'].values() for f in it.get('flags', [])]
    check(not any('valleys disagree' in f or 'Review integration or assignment of calibration' in f for f in flags), 'no spurious standard-valley warnings')
    restored = m.processing_update_calibration(p, selected, 'N', '3', True, 'test: restore standard')
    check(not math.isclose(item(restored, 6, 'N')['value'], item(selected, 6, 'N')['value'], abs_tol=1e-4), 'restoring a standard changes dependent results')
    manual = m.processing_peak_preview(p, selected, 6, 'H', h['start'], h['saved_end'], baseline_left=None, baseline_right=None, assignment_confirmed=True)
    check(not math.isclose(item(manual, 6, 'H')['value'], h['value'], abs_tol=1e-4), 'moving an end point changes the result')
    defaults, decisions = m.default_report_preview(p, selected)
    check(decisions['confirmed'] == [(7, 'S')] and item(defaults, 7, 'S')['value'] > 3, 'missed sulfur peak of Demo A - 2 reported')
    m.apply_native_processing(p, defaults, 'test', m.DEFAULT_REPORT_REASON, include_review=True)
    g = {r.name: r for r in m.compute_results(p, reporting=True)}
    check(g['Demo A'].counts == dict(zip(m.ELEMENTS, (3, 3, 3, 2))), 'Demo A: only the missing S left out (n = 3, 3, 3, 2)')
    check(all(v == 2 for v in g['Demo B'].counts.values()), 'Demo B: failed portion left out (n = 2)')
    check(g['Demo C'].counts['S'] == 3 and g['Demo C'].means['S'] == 0, 'Demo C: S reported as 0 in all three portions')
    check(not m.report_readiness(p)['ready'], 'not signed off automatically')
    # file repair
    r = m.full_demo_project(folder, repair=True)
    check({x.index for x in r.records if x.dat_info.get('status') == 'identity_mismatch'} == {6, 7}, 'file repair: both swapped files found')
    props = m.suggest_data_files(r)
    check({i: Path(v['path']).name for i, v in props.items() if v['action'] == 'link'} == {6: 'SYN007.DAT', 7: 'SYN006.DAT'}, 'file repair: correct files proposed')
    before = hashes(folder)
    for idx, s in props.items():
        m.link_data_file(r, idx, s['path'], 'test', 'confirm demo repair')
    check(all(x.dat_info.get('status') == 'verified' for x in r.records), 'file repair: all 15 records verified after confirmation')
    check(hashes(folder) == before, 'demonstration files unchanged by the repair')
    # export: every output says synthetic
    paths = m.export_analysis(p, tmp / 'out', extra_files=True, draft=True)
    for name in ('CHNS results - review', 'CHNS results - report', 'Detailed calculations', 'Detailed explanations'):
        with zipfile.ZipFile(paths[name]) as z:
            text = ''.join(z.read(n).decode('utf-8', 'ignore') for n in z.namelist() if n.endswith('.xml'))
        check('SYNTHETIC' in text, f'{name}: marked SYNTHETIC')
    data = json.loads(Path(paths['Project']).read_text(encoding='utf-8'))
    reopened = m.load_project(paths['Project'])
    check(reopened.demo and reopened.settings.reference_table == m.DEMO_REFERENCE_NAME, 'reopened project keeps demo flag and its reference')
    rg = {x.name: x for x in m.compute_results(reopened, reporting=True)}
    check(all(rg[k].counts == v.counts and rg[k].means == v.means for k, v in g.items()), 'reopened project gives identical results')
    o = m.import_file(folder / 'SYNTHETIC_main' / 'SYNTHETIC_CHNS.MTH')
    check(o.demo and o.settings.reference_table == m.DEMO_REFERENCE_NAME and o.input_warnings[0] == m.DEMO_WARNING,
          'demonstration files opened with Open .MTH are recognized and labelled too')
    # isolation from real runs
    check(not m.certificate_batch_date(m.DEMO_REFERENCE_NAME), 'demo reference is undated, so never a default for a real run')
    if REAL:
        q = m.import_file(REAL)
        check(q.settings.reference_table != m.DEMO_REFERENCE_NAME and not q.demo, 'a real run opened after the demo does not use the demo reference')
except Exception:
    traceback.print_exc(); bad += 1
print(f'{ok} passed, {bad} failed')
sys.exit(1 if bad else 0)
