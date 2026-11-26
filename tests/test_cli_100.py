"""CHNSetti 1.0.0: the command line with --process-native gives the same report as the wizard.
Usage: python test_cli_100.py src/chnsetti.py RUN.MTH   (a run with a check material, e.g. demo/SYNTHETIC_main/SYNTHETIC_CHNS.MTH)"""
import os, sys, io, glob, tempfile, contextlib, importlib.util, traceback
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
s = importlib.util.spec_from_file_location('c', sys.argv[1]); C = importlib.util.module_from_spec(s); sys.modules['c'] = C; s.loader.exec_module(C)
RUN = sys.argv[2]
results = []
def check(name, ok, detail=''):
    results.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok or not detail else ' — ' + str(detail)), flush=True)


def report_cells(folder):
    import openpyxl
    path = next(p for p in glob.glob(os.path.join(folder, '**', '*.xlsx'), recursive=True) if 'report' in os.path.basename(p).lower())
    wb = openpyxl.load_workbook(path, data_only=True)
    out = {}
    for ws in wb.worksheets:
        if ws.title.lower().startswith('run information'):
            continue  # times of export differ
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is not None:
                    out[(ws.title, cell.coordinate)] = cell.value
    return out


def cli(*extra):
    tmp = tempfile.mkdtemp()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        C.main(['analyze', RUN, '-o', tmp, *extra])
    return tmp, buf.getvalue()


def gui():
    try:
        app = QApplication.instance(); w = [x for x in app.topLevelWidgets() if isinstance(x, QWizard)][0]; w.resize(1366, 860)
        w.next(); w.pages[1].import_selected_file(RUN); app.processEvents()
        for _ in range(5): w.next(); app.processEvents()
        check('wizard: step 6 with CHNSetti\'s results in the report', w.currentId() == 6 and w.project.processing.get('report_basis') == 'chnsetti')
        wizard_folder = tempfile.mkdtemp(); C.export_analysis(w.project, wizard_folder, draft=True)
        wizard = report_cells(wizard_folder)
        folder, out = cli('--process-native')
        line = report_cells(folder)
        diff = [(k, wizard.get(k), line.get(k)) for k in sorted(set(wizard) | set(line), key=str) if wizard.get(k) != line.get(k)]
        check('command line --process-native: the same report as the wizard', not diff, diff[:5])
        check('command line says what it did (default choice, small-peak rule)', 'Default choice of standards' in out and 'CHNSetti results in the report' in out, out[:300])
        p = C.import_file(RUN)
        check('command line keeps the default certificate batch when --reference is omitted', p.settings.reference_table != C.NO_REFERENCE)
        folder2, _ = cli()
        instrument = report_cells(folder2)
        check('without --process-native the instrument\'s results are exported (as before)', instrument != line)
        folder3, out3 = cli('--process-native', '--all-standards')
        check('--all-standards keeps every standard', 'Default choice of standards' not in out3 and report_cells(folder3) != line)
    except Exception as exc:
        traceback.print_exc(); check('cases raised unexpectedly', False, repr(exc))
    print(f'{sum(results)} passed, {len(results) - sum(results)} failed', flush=True); os._exit(0 if all(results) else 1)


from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QWizard, QMessageBox
QMessageBox.exec = lambda self: 0
orig = QApplication.exec
QApplication.exec = lambda *a: (QTimer.singleShot(200, gui), orig())[1]
C.launch_gui()
