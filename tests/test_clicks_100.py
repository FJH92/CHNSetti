"""CHNSetti 1.0.0: what a click in a table does. Usage: python test_clicks_100.py src/chnsetti.py RUN.MTH"""
import os, sys, traceback, importlib.util
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
s = importlib.util.spec_from_file_location('c', sys.argv[1]); C = importlib.util.module_from_spec(s); sys.modules['c'] = C; s.loader.exec_module(C)
from PySide6.QtWidgets import QApplication, QMessageBox, QWizard, QDialog
from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest
QMessageBox.exec = lambda self: 0
QDialog.exec = lambda self: QDialog.Accepted
results = []
def check(name, ok, detail=''):
    results.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok or not detail else ' — ' + str(detail)), flush=True)
def go():
    try:
        app = QApplication.instance(); w = [x for x in app.topLevelWidgets() if isinstance(x, QWizard)][0]; w.resize(1366, 860)
        w.next(); w.pages[1].import_selected_file(sys.argv[2]); w.next(); app.processEvents()
        ip = w.pages[2]; records = w.project.records
        check('step 2: a chromatogram under the table', ip.trace_plot.isVisible())
        i = next(k for k, r in enumerate(records) if C._processing_trace(r) and r.role == 'Sample')
        ip.table.setCurrentCell(i, 1); app.processEvents()
        check('step 2: click a row → its chromatogram', ip.trace_plot.trace is C._processing_trace(records[i]) and records[i].name in ip.trace_plot.title)
        check('step 2: read-only', not ip.trace_plot.editable and not ip.trace_plot.others_editable)
        w.next(); w.next(); app.processEvents(); kp = w.pages[4]
        row = next(k for k, r in enumerate(kp.rows) if r is not None and r.role == 'Calibration')
        kp.table.setCurrentCell(row, kp.FIRST + 1); app.processEvents()
        check('step 4: the tooltip says what a click does', kp.table.item(row, kp.FIRST + 1).toolTip().endswith('Click to show it on the curve.'))
        rect = kp.table.visualItemRect(kp.table.item(row, kp.FIRST + 1))
        QTest.mouseDClick(kp.table.viewport(), Qt.LeftButton, Qt.NoModifier, rect.center()); app.processEvents()
        check('step 4: a double-click stays in step 4', w.currentId() == 4)
        kp.see_peak(); app.processEvents()
        check('step 4: See peak still opens step 5', w.currentId() == 5)
        cp = w.pages[5]; r0 = next(k for k, c in enumerate(cp.row_context) if c)
        check('step 5: the tooltip says what a click does', cp.table.item(r0, cp.FIRST + 1).toolTip().endswith('Click to show the peak.'))
        check('step 5: no hint on the name column', 'Click to show' not in cp.table.item(r0, 0).toolTip())
        w.next(); app.processEvents(); rp = w.pages[6]
        mean = next(k for k, c in enumerate(rp.row_context) if c and c.get('statistic') == 'mean' and len([r for r in records if r.index in rp.row_groups[k].indices and C._processing_trace(r)]) > 1)
        rp.table.setCurrentCell(mean, rp.FIRST + 1); app.processEvents()
        portions = rp.peak_portions()
        check('step 6: avg. row → its portions to choose from', len(portions) > 1 and all(r.index in rp.row_groups[mean].indices for r in portions))
        check('step 6: the tooltip says so', 'Show peak: choose a portion.' in rp.table.item(mean, rp.FIRST + 1).toolTip())
        rp.choose_portion = lambda choices: None
        rp.show_peak(); app.processEvents()
        check('step 6: closing the choice stays in step 6', w.currentId() == 6)
        rp.choose_portion = lambda choices: choices[1].index
        rp.show_peak(); app.processEvents()
        check('step 6: the chosen portion opens', w.currentId() == 5 and w.review_panel.record is portions[1] and w.review_panel.element == 'C')
        w.next(); app.processEvents()
        portion = next(k for k, c in enumerate(rp.row_context) if c and c.get('statistic') == 'portion' and C._processing_trace(next(r for r in records if r.index == c['measurement_index'])))
        rp.table.setCurrentCell(portion, 0); app.processEvents(); rp.show_peak(); app.processEvents()
        record = next(r for r in records if r.index == rp.row_context[portion]['measurement_index'])
        check('step 6: from the name cell → the first element with a peak', w.currentId() == 5 and w.review_panel.record.index == record.index and w.review_panel.element in C.ELEMENTS,
              (w.currentId(), w.review_panel.record.name, record.name, w.review_panel.element, rp.current_measurement()))
    except Exception:
        traceback.print_exc(); results.append(False)
    print(f'{sum(results)} passed, {results.count(False)} failed', flush=True); os._exit(0 if all(results) else 1)
orig = QApplication.exec
QApplication.exec = lambda *a: (QTimer.singleShot(200, go), orig())[1]
C.launch_gui()
