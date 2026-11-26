"""CHNSetti 1.4.9: boundaries between detector points, the automatic method choice, the calibration equation.
Usage: python test_149.py CHNSetti_1_4_9.py RUN.MTH"""
import os, sys, math, tempfile, traceback, importlib.util
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
s = importlib.util.spec_from_file_location('c', sys.argv[1]); C = importlib.util.module_from_spec(s); sys.modules['c'] = C; s.loader.exec_module(C)
from PySide6.QtWidgets import QApplication, QMessageBox, QWizard, QDialog, QLineEdit
from PySide6.QtCore import QTimer
QMessageBox.exec = lambda self: 0
def fake_exec(self):
    for e in self.findChildren(QLineEdit):
        if not e.text().strip(): e.setText('automated test')
    return QDialog.Accepted
QDialog.exec = fake_exec
results = []
def check(name, ok, detail=''):
    results.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok or not detail else ' — ' + str(detail)), flush=True)
def go():
    try:
        app = QApplication.instance(); w = [x for x in app.topLevelWidgets() if isinstance(x, QWizard)][0]
        # engine: whole-point boundaries give the 1.4.8 area exactly; positions in between are continuous
        sig = [5.0, 5.0, 9.0, 30.0, 18.0, 8.0, 6.0, 5.0, 5.0]
        whole = C.proc_integrate(sig, 1, 7, 'linear', 5.0, 5.0)['area']
        check('whole-point boundaries use the original integration', whole == C._proc_integrate_points(sig, 1, 7, 'linear', 5.0, 5.0)['area'])
        part = [C.proc_integrate(sig, 1, 6 + f, 'linear', 5.0, C._proc_interp(sig, 6 + f))['area'] for f in (0, .25, .5, .75)]
        check('area changes monotonically between two points', part == sorted(part), part)
        check('proc_integrate accepts 1.0 as whole point 1', C.proc_integrate(sig, 1.0, 7.0)['start'] == 1 and isinstance(C.proc_integrate(sig, 1.0, 7.0)['start'], int))
        w.next(); w.pages[1].import_selected_file(sys.argv[2]); w.next(); w.next(); w.next(); w.next(); app.processEvents()
        rp = w.pages[5]; panel = rp.panel
        check('advanced automatic boundaries by default', panel.preview['settings'].get('boundary_method') == 'advanced')
        rec = next(r for r in w.project.records if r.role == 'Sample' and C._processing_trace(r))
        panel.show_record(rec.index, 'C'); app.processEvents()
        cur = dict(panel.current_result()); cur['end'] = cur['end'] + 0.37
        panel.plot_edit(cur, 'end'); app.processEvents()
        got = panel.current_result()
        check('panel keeps an end between detector points', abs(got['end'] - (round(cur['end'], 2))) < 1e-9 and got['end'] != round(got['end']), got['end'])
        check('baseline point lies on the trace', abs(got['baseline_right'] - panel.plot.trace_value(got['end'])) < 1e-9)
        lines = panel.calibration.equation_lines()
        fit = panel.preview['calibrations']['C']
        if fit.get('slope') is None:
            check('no equation while the curve is unavailable', lines == [], lines)
        else:
            check('calibration equation shown', lines and lines[0] == 'Carbon: peak area = K × carbon mass' and lines[1].startswith('K = ') and 'standards' in lines[2], lines)
            check('equation is the fitted line', C.format_factor(fit['slope']) in lines[1], lines)
            check('R² in the box tooltip', 'R²' in panel.calibration.equation_tooltip(), panel.calibration.equation_tooltip())
        folder = tempfile.mkdtemp(); path = os.path.join(folder, 'p.CHNSetti.json'); w.project_path = path
        check('save with a boundary between points', w.save_current_project())
        staged = (C.load_workspace(path)['pending_edits'].get('native_processing_editor') or {}).get('preview')
        item = staged['records'][str(rec.index)]['elements']['C']
        check('saved project keeps the position', abs(item['end'] - got['end']) < 1e-12 and math.isclose(item['area'], got['area']))
        panel.apply_to_report(); app.processEvents()
        rec = next(r for r in w.project.records if r.index == rec.index)  # applying replaces the record objects
        val = C.report_value(rec, 'C'); applied = w.project.processing['active_preview']['records'][str(rec.index)]['elements']['C']
        check('applied result keeps the position', abs(applied['end'] - got['end']) < 1e-12)
        if rec.processed_results['C'].get('reportable'):
            check('report value from that integration', val is not None and math.isclose(val, applied['value'], abs_tol=1e-12), (val, applied.get('value')))
        else:
            check('result that needs review is held back from the report', val is None or not math.isclose(val, applied.get('value') or -1, abs_tol=1e-12))
        # switching the automatic method
        w.set_boundary_method('classical'); app.processEvents()
        check('classical chosen in settings', C.processing_default_settings(w.project)['boundary_method'] == 'classical')
        expected = C.preview_native_processing(w.project, C.processing_default_settings(w.project))
        same = all(expected['records'][k]['elements'][e].get('start') == v['elements'][e].get('start') and
                   expected['records'][k]['elements'][e].get('end') == v['elements'][e].get('end')
                   for k, v in panel.preview['records'].items() for e in C.ELEMENTS)
        check('panel shows the classical proposals', same and not panel.edited)
        w.set_boundary_method('advanced'); app.processEvents()
        check('back to advanced', panel.preview['settings']['boundary_method'] == 'advanced' and C.processing_default_settings(w.project)['boundary_method'] == 'advanced')
        w.next(); w.next(); w.next(); ep = w.pages[7]; ep.path.setText(tempfile.mkdtemp())
        check('export succeeds', ep.generate())
    except Exception:
        traceback.print_exc(); results.append(False)
    print(f'{sum(results)} passed, {results.count(False)} failed', flush=True); os._exit(0 if all(results) else 1)
orig = QApplication.exec
QApplication.exec = lambda *a: (QTimer.singleShot(200, go), orig())[1]
C.launch_gui()
