"""GUI: the full demonstration opens from the menu of step 1 and runs through all seven steps.
Usage: python test_full_demo_gui_100.py src/chnsetti.py"""
import sys, os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import importlib.util, traceback
s = importlib.util.spec_from_file_location('c', sys.argv[1]); C = importlib.util.module_from_spec(s); sys.modules['c'] = C; s.loader.exec_module(C)
from PySide6.QtWidgets import QApplication, QMessageBox, QWizard, QToolButton
from PySide6.QtCore import QTimer
QMessageBox.exec = lambda self: 0
res = {'ok': 0, 'bad': 0}
def check(c, t):
    res['ok' if c else 'bad'] += 1; print(('PASS ' if c else 'FAIL ') + t)
def go():
    try:
        app = QApplication.instance(); w = [x for x in app.topLevelWidgets() if isinstance(x, QWizard)][0]
        w.next(); page = w.pages[1]
        more = next(b for b in page.findChildren(QToolButton) if b.text() == 'More import options')
        demos = next(a.menu() for a in more.menu().actions() if a.menu() and 'Demonstration' in a.text())
        names = [a.text() for a in demos.actions()]
        check(names == ['Full run with detector signals', 'File repair: two data files swapped', 'Results table only (no detector signals)'], 'three demonstrations in the menu')
        demos.actions()[0].trigger(); app.processEvents()
        check(w.project is not None and w.project.demo and len(w.project.records) == 15, 'full demonstration opened')
        check('SYNTHETIC DEMONSTRATION' in w.windowTitle() and 'SYNTHETIC' in w.steps.save_status.text(), 'window title and step list say SYNTHETIC')
        for _ in range(5): w.next(); app.processEvents()
        g = {x.name: x for x in C.compute_results(w.project, reporting=True)}
        check(g['Demo A'].counts['S'] == 2 and g['Demo B'].counts['N'] == 2 and g['Demo C'].means['S'] == 0, 'step 6: failed portions left out, zeros kept')
        w.next(); app.processEvents()
        check(C.report_readiness(w.project)['blockers'] == ['Sign off the results as final (step 7).'], 'step 7: only the sign-off is left')
        w.maybe_save_changes = lambda *a: True   # answer 'Discard' to the unsaved-changes question
        demos.actions()[1].trigger(); app.processEvents()
        bad = [r.index for r in w.project.records if (r.dat_info or {}).get('status') == 'identity_mismatch']
        check(bad == [6, 7], 'file-repair demonstration shows the two swapped files')
        demos.actions()[2].trigger(); app.processEvents()
        check(w.project.demo and w.project.source_name.startswith('Embedded synthetic demo'), 'results-only demonstration still available')
    except Exception:
        traceback.print_exc(); res['bad'] += 1
    print(f"{res['ok']} passed, {res['bad']} failed"); os._exit(1 if res['bad'] else 0)
orig = QApplication.exec
QApplication.exec = lambda *a: (QTimer.singleShot(200, go), orig())[1]
C.launch_gui()
