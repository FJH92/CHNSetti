"""Headless smoke test: every result cell, every measurement trace, larger editor, apply and export.

Usage: python smoke_gui_runs.py path/to/CHNSetti_1_4_2.py RUN.MTH [RUN.MTH ...] | demo
Exits non-zero if any step raises (including exceptions inside Qt slots).
"""
import os, sys, tempfile, traceback, importlib.util
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
spec = importlib.util.spec_from_file_location('chnsetti', sys.argv[1]); C = importlib.util.module_from_spec(spec)
sys.modules['chnsetti'] = C; spec.loader.exec_module(C)
from PySide6.QtWidgets import QApplication, QMessageBox, QWizard, QDialog, QLineEdit
from PySide6.QtCore import QTimer
QMessageBox.exec = lambda self: 0
def fake_exec(self):
    for edit in self.findChildren(QLineEdit):
        if not edit.text().strip(): edit.setText('smoke test')
    return QDialog.Accepted
QDialog.exec = fake_exec
errors = []
sys.excepthook = lambda *exc: (errors.append(''.join(traceback.format_exception(*exc))), traceback.print_exception(*exc))

def go():
    app = QApplication.instance(); w = [x for x in app.topLevelWidgets() if isinstance(x, QWizard)][0]
    for run in sys.argv[2:]:
        try:
            w.pending_edits = {}; w.saved_digest = None; w.project = None
            if w.currentId() != 1:
                w.restart(); w.next()
            if run == 'demo': w.pages[1].load_demo()
            else: w.pages[1].import_selected_file(run)
            w.saved_digest = C.project_content_digest(w.project, w.capture_workspace())  # treat as saved: no prompts
            w.next(); w.next(); w.next(); app.processEvents()
            native = type(w.currentPage()).__name__ == 'CalibrationPage'
            if native:  # step 4: every element and standard, with the check-material box
                kp = w.pages[4]
                for e in C.ELEMENTS:
                    kp.set_element(e)
                    for row in range(kp.table.rowCount()): kp.table.setCurrentCell(row, kp.FIRST + C.ELEMENTS.index(e))
                    kp.curve.repaint(); kp.curve.check_lines()
                app.processEvents()
                w.next(); app.processEvents(); cp = w.pages[5]; panel = cp.panel  # step 5: every measurement and element
                assert w.currentPage() is cp, type(w.currentPage()).__name__
                cp.attention.setChecked(True); cp.attention.setChecked(False)
                for row in range(cp.table.rowCount()):
                    for col in range(cp.table.columnCount()): cp.table.setCurrentCell(row, col)
                for record in w.project.records:
                    for e in C.ELEMENTS:
                        panel.show_record(record.index, e, zoom=True); panel.toggle_view(); panel.toggle_view()
                cp.show_chromatogram(); app.processEvents()
                w.next(); app.processEvents()
            rp = w.pages[6]
            assert w.currentPage() is rp, type(w.currentPage()).__name__
            for row in range(rp.table.rowCount()):
                for col in range(rp.table.columnCount()):
                    rp.table.setCurrentCell(row, col)
            app.processEvents()
            rp.show_questions(); rp.show_group_details(); rp.show_calculation()
            if native:
                rp.apply_to_report(); app.processEvents()
            w.next(); ep = w.pages[7]; ep.path.setText(tempfile.mkdtemp()); ok = ep.generate()
            print(('OK   ' if ok else 'FAIL ') + os.path.basename(os.path.dirname(run)) + ('  native panel' if native else '  no traces'), flush=True)
            if not ok: errors.append('export failed ' + run)
        except Exception:
            errors.append(traceback.format_exc()); traceback.print_exc()
    print(f'{len(errors)} error(s)', flush=True)
    os._exit(1 if errors else 0)

orig = QApplication.exec
QApplication.exec = lambda *a: (QTimer.singleShot(200, go), orig())[1]
C.launch_gui()
