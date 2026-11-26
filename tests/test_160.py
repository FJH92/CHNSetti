"""CHNSetti 1.0.0: step 4 Calibration, step 5 Chromatograms, step 6 Results.
Usage: python test_160.py CHNSetti_1_6_0.py RUN.MTH"""
import os, sys, math, tempfile, traceback, importlib.util
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
s = importlib.util.spec_from_file_location('c', sys.argv[1]); C = importlib.util.module_from_spec(s); sys.modules['c'] = C; s.loader.exec_module(C)
from PySide6.QtWidgets import QApplication, QMessageBox, QWizard, QDialog, QLineEdit
from PySide6.QtCore import QTimer, QPoint, Qt
from PySide6.QtTest import QTest
QMessageBox.exec = lambda self: 0
def fake_exec(self):
    for e in self.findChildren(QLineEdit):
        if not e.text().strip(): e.setText('automated test')
    return QDialog.Accepted
QDialog.exec = fake_exec
results = []
def check(name, ok, detail=''):
    results.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok or not detail else ' — ' + str(detail)), flush=True)
def area_text(v): return f'{float(v):,.0f}'.replace(',', ' ')
def go():
    try:
        app = QApplication.instance(); w = [x for x in app.topLevelWidgets() if isinstance(x, QWizard)][0]; w.resize(1400, 950)
        check('seven steps', w.steps.TITLES == ('Files', 'Identification', 'Calculation rules', 'Calibration', 'Chromatograms', 'Results', 'Generate'))
        w.next(); w.pages[1].import_selected_file(sys.argv[2]); w.next(); w.next(); app.processEvents()
        rules = w.pages[3]
        check('method choice in Calculation rules', rules.boundary.isVisible() and rules.boundary.currentData() == 'advanced')
        # ---------------- step 4: Calibration (before the chromatograms since 1.0.0)
        w.next(); app.processEvents()
        kp = w.pages[4]; panel = kp.panel
        sample = next(r for r in w.project.records if r.role == 'Sample' and C._processing_trace(r))
        check('step 4 is Calibration, one curve, element buttons', w.currentPage() is kp and kp.curve.isVisible() and len(kp.element_buttons) == 4)
        standards = [r for r in kp.rows if r is not None and r.role == 'Calibration']
        kp.table.setCurrentCell(kp.rows.index(standards[0]), kp.FIRST + 1); app.processEvents()
        point = next(p for p in panel.preview['calibrations']['C']['points'] if str(p['id']) == str(standards[0].index))
        check('recovery listed and standard ringed', kp.table.item(kp.rows.index(standards[0]), kp.FIRST + 1).text() == f"{point['recovery_pct']:.1f} %"
              and str(kp.curve.selected_id) == str(standards[0].index) and kp.element == 'C' and kp.element_buttons['C'].isChecked())
        check('equation on the curve', kp.curve.equation_lines() and kp.curve.equation_lines()[0] == 'Carbon: peak area = K × carbon mass')
        kp.element_buttons['S'].click(); app.processEvents()
        check('element buttons switch the curve', kp.element == 'S' and kp.curve.element == 'S')
        kp.element_buttons['C'].click(); app.processEvents()
        kp.curve.resize(700, 320); kp.curve.repaint(); app.processEvents()
        other = standards[1]
        q = next(h[0] for h in kp.curve._hits if h[1] == str(other.index))
        before = panel.preview['records'][str(sample.index)]['elements']['C']['value']
        QTest.mouseClick(kp.curve, Qt.LeftButton, Qt.NoModifier, QPoint(round(q.x()), round(q.y()))); app.processEvents()
        check('one click excludes; list shows it', kp.table.item(kp.rows.index(other), kp.FIRST + 1).text() == 'excluded')
        after = panel.preview['records'][str(sample.index)]['elements']['C']['value']
        check('sample results follow the curve', not math.isclose(after, before, rel_tol=1e-12))
        kp.undo(); app.processEvents()
        check('undo restores it', kp.table.item(kp.rows.index(other), kp.FIRST + 1).text() != 'excluded'
              and math.isclose(panel.preview['records'][str(sample.index)]['elements']['C']['value'], before, rel_tol=1e-12))
        kp.table.setCurrentCell(kp.rows.index(standards[2]), kp.FIRST + 2); app.processEvents()
        kp.see_peak(); app.processEvents()
        check('See peak opens that standard in step 5', w.currentId() == 5 and panel.record is standards[2] and panel.element == 'H')
        w.back(); app.processEvents()
        check('Back returns to the calibration', w.currentPage() is kp and kp.selected is standards[2])
        # ---------------- step 5: Chromatograms
        w.next(); app.processEvents()
        cp = w.pages[5]
        check('step 5 is Chromatograms', w.currentPage() is cp and panel.parent() is cp.splitter)
        titles = [cp.table.item(r, 0).text() for r, c in enumerate(cp.row_context) if c is None]
        check('standards first, then check material and samples', titles[0] == 'Standards' and titles[-1] == 'Samples', titles)
        check('no calibration curve and no Apply in step 5', not panel.calibration.isVisible() and panel.apply_button.isHidden()
              and not panel.range_label.isVisible())
        first = next(i for i, c in enumerate(cp.row_context) if c)
        cp.table.setCurrentCell(first, cp.FIRST + 1); app.processEvents()
        rec = next(r for r in w.project.records if r.index == cp.row_context[first]['measurement_index'])
        item = panel.preview['records'][str(rec.index)]['elements']['C']
        check('table shows the carbon % w/w of the first standard', cp.table.item(first, cp.FIRST + 1).text() == f"{item['value']:.4f}"
              and cp.table.horizontalHeaderItem(cp.FIRST + 1).text() == 'C % w/w', cp.table.item(first, cp.FIRST + 1).text())
        check('peak area in the cell tooltip', C.format_area(item['area']) in cp.table.item(first, cp.FIRST + 1).toolTip(), cp.table.item(first, cp.FIRST + 1).toolTip())
        check('click opens that peak', panel.record is rec and panel.element == 'C' and rec.role == 'Calibration')
        txt = panel.result_label.text()
        check('result line says % w/w, known composition and peak area in detector units',
              f"Carbon found: {item['value']:.2f} % w/w" in txt and 'known composition' in txt and 'peak area ' + C.format_area(item['area']) + ' (detector units)' in txt, txt)
        cp.focus_measurement(sample.index, 'H'); app.processEvents()
        cur = dict(panel.current_result()); cur['end'] = cur['end'] - 30
        panel.plot_edit(cur, 'end'); app.processEvents()
        row = next(i for i, c in enumerate(cp.row_context) if c and c['measurement_index'] == sample.index)
        new_area = panel.preview['records'][str(sample.index)]['elements']['H']['area']
        new_value = panel.preview['records'][str(sample.index)]['elements']['H']['value']
        check('editing a peak updates its value in the list', cp.table.item(row, cp.FIRST + 2).text() == f"{new_value:.4f}"
              and C.format_area(new_area) in cp.table.item(row, cp.FIRST + 2).toolTip()
              and panel.record is sample)
        cp.attention.setChecked(True); app.processEvents()
        shown = [c['measurement_index'] for c in cp.row_context if c]
        flagged = [r.index for _, rs in C.review_measurements(w.project) for r in rs
                   if any(C.peak_attention(r, panel.preview['records'].get(str(r.index), {}).get('elements', {}).get(e)) for e in C.ELEMENTS)] \
            if hasattr(C, 'review_measurements') else shown
        check('"Only peaks that need a look" filters the list', len(shown) <= len([c for c in cp.row_context]) and set(shown) <= set(flagged) | {sample.index})
        cp.attention.setChecked(False); app.processEvents()
        # ---------------- step 6
        w.next(); app.processEvents()
        rp = w.pages[6]
        check('step 6 is Results without a chromatogram', w.currentPage() is rp and not hasattr(rp, 'splitter') or rp.panel.parent() is not rp)
        check('by default the report uses CHNSetti\'s results (green banner, no Apply needed)', rp.banner.isVisible() and 'uses CHNSetti' in rp.banner_text.text()
              and not rp.apply_button.isVisible() and panel.preview_in_report(), rp.banner_text.text())
        check('applied by default with its reason', any(d.get('reason') == C.DEFAULT_REPORT_REASON for d in w.project.decisions))
        rp.use_instrument_results(); app.processEvents()
        check('"Use the instrument\'s results instead": banner offers Apply again', rp.banner.isVisible() and 'not in the report yet' in rp.banner_text.text()
              and rp.apply_button.isVisible() and w.project.processing.get('report_basis') == 'instrument', rp.banner_text.text())
        changed = panel.differences()
        check('banner counts the values that would change', (str(changed) in rp.banner_text.text()) if changed else 'stay the same' in rp.banner_text.text())
        w.back(); w.next(); app.processEvents()
        check('the choice of the instrument\'s results is kept on returning to step 6', 'not in the report yet' in rp.banner_text.text())
        marked = []
        for r, ctx in enumerate(rp.row_context):
            if ctx and ctx.get('measurement_index') and ctx.get('statistic') == 'portion':
                for col in range(rp.FIRST, rp.FIRST + 4):
                    it = rp.table.item(r, col)
                    if it and it.foreground().color().name().upper() == '#C2410C':marked.append((r, col))
        expected = []
        for r, ctx in enumerate(rp.row_context):
            if ctx and ctx.get('measurement_index') and ctx.get('statistic') == 'portion':
                rec = next(x for x in w.project.records if x.index == ctx['measurement_index'])
                for col, e in enumerate(C.ELEMENTS, rp.FIRST):
                    if C.report_value(rec, e) is not None and rp.range_note(rec, e):expected.append((r, col))
        check('values outside the standards\' range are marked (and only those)', marked == expected and all('extrapolated' in rp.table.item(r, c).toolTip() for r, c in marked), (len(marked), len(expected)))
        row = next(i for i, c in enumerate(rp.row_context) if c and c.get('measurement_index') == sample.index)
        rp.table.setCurrentCell(row, rp.FIRST + 1); app.processEvents()
        rp.show_peak(); app.processEvents()
        check('Show peak opens the value in step 5', w.currentId() == 5 and panel.record.index == sample.index and panel.element == 'C')
        w.next(); app.processEvents()
        check('Next returns to the results', w.currentPage() is rp)
        rp.apply_to_report(); app.processEvents()
        check('Apply in step 6: banner turns green again', 'uses CHNSetti' in rp.banner_text.text() and not rp.apply_button.isVisible()
              and w.project.processing.get('report_basis') == 'chnsetti')
        # ---------------- method choice in step 3
        w.go_to_step(3); app.processEvents()
        cur = dict(panel.current_result()); panel.plot_edit(dict(cur, end=cur['end'] - 5), 'end'); app.processEvents()
        rules.boundary.setCurrentIndex(rules.boundary.findData('classical')); rules.boundary.activated.emit(rules.boundary.currentIndex()); app.processEvents()
        check('changing the method with edits asks first (cancel keeps them)', rules.boundary.currentData() == 'advanced' and panel.edited)
        while panel.history: panel.undo()
        rules.boundary.setCurrentIndex(rules.boundary.findData('classical')); rules.boundary.activated.emit(rules.boundary.currentIndex()); app.processEvents()
        check('without edits the method changes at once', panel.preview['settings']['boundary_method'] == 'classical')
        rules.boundary.setCurrentIndex(rules.boundary.findData('advanced')); rules.boundary.activated.emit(rules.boundary.currentIndex()); app.processEvents()
        for _ in range(4): w.next(); app.processEvents()
        ep = w.pages[7]
        check('step 7 is Generate', w.currentPage() is ep)
        ep.path.setText(tempfile.mkdtemp()); check('export succeeds', ep.generate())
        # ---------------- no detector traces: steps 4 and 5 skipped
        w.pending_edits = {}; w.saved_digest = None; w.project = None
        w.restart(); w.next(); w.pages[1].load_demo()
        w.saved_digest = C.project_content_digest(w.project, w.capture_workspace())
        w.next(); w.next(); w.next(); app.processEvents()
        check('no traces: steps 4 and 5 skipped', w.currentId() == 6 and 'not needed' in w.steps.labels[3].text() and 'not needed' in w.steps.labels[4].text())
        check('no banner and no Show peak without traces', not w.pages[6].banner.isVisible() and not w.pages[6].peak_button.isEnabled())
        w.back(); app.processEvents()
        check('back from results goes to rules', w.currentId() == 3)
    except Exception:
        traceback.print_exc(); results.append(False)
    print(f'{sum(results)} passed, {results.count(False)} failed', flush=True); os._exit(0 if all(results) else 1)
orig = QApplication.exec
QApplication.exec = lambda *a: (QTimer.singleShot(200, go), orig())[1]
C.launch_gui()
