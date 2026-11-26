"""Calibration curve: one click excludes a standard, a second click restores it, results follow.
Drawing a peak: dragging across the trace integrates an element that had no peak.
Usage: python test_calibration_and_new_peak.py CHNSetti_1_6_0.py RUN.MTH"""
import os, sys, math, tempfile, traceback, importlib.util
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
s = importlib.util.spec_from_file_location('c', sys.argv[1]); C = importlib.util.module_from_spec(s); sys.modules['c'] = C; s.loader.exec_module(C)
from PySide6.QtWidgets import QApplication, QMessageBox, QWizard, QDialog, QLineEdit
from PySide6.QtCore import QTimer, QPoint, QPointF, Qt
from PySide6.QtTest import QTest
QMessageBox.exec = lambda self: 0
def fake_exec(self):
    for edit in self.findChildren(QLineEdit):
        if not edit.text().strip(): edit.setText('test reason')
    return QDialog.Accepted
QDialog.exec = fake_exec
results = []
def check(name, ok, detail=''):
    results.append(ok); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else f'  {detail}'), flush=True)
def go():
    try:
        app = QApplication.instance(); w = [x for x in app.topLevelWidgets() if isinstance(x, QWizard)][0]; w.resize(1400, 950)
        w.next(); w.pages[1].import_selected_file(sys.argv[2]); w.next(); w.next(); w.next(); app.processEvents()
        kp = w.pages[4]; panel = kp.panel; cal = kp.curve
        check('step 4 is the calibration', w.currentPage() is kp)
        kp.set_element('C'); app.processEvents()
        cal.resize(700, 300); cal.repaint(); app.processEvents()
        check('calibration curve shown for the selected element', cal.isVisible() and cal.element == 'C' and len(cal.points()) >= 2)
        if panel.preview['calibrations']['C'].get('slope') is None:
            # A standard without a usable peak blocks the curve: one click on it must exclude it and unblock the curve.
            q, ident, point = next(h for h in cal._hits if h[2].get('area') is None or not h[2].get('assignment_confirmed', True))
            QTest.mouseClick(cal, Qt.LeftButton, Qt.NoModifier, QPoint(round(q.x()), round(q.y()))); app.processEvents()
            check('clicking a standard without a peak excludes it and unblocks the curve',
                  panel.preview['calibrations']['C'].get('slope') is not None, panel.preview['calibrations']['C'].get('flags'))
            cal.repaint(); app.processEvents()
        checks = [i for i, r in enumerate(kp.rows) if r is not None and r.role == 'Check']
        if checks:
            kp.table.setCurrentCell(checks[0], kp.FIRST + 1); app.processEvents(); cal.repaint()
            check('check material marked on the curve', bool(cal.sample) or not C._finite_percentage(
                panel.preview['records'][str(kp.rows[checks[0]].index)]['elements']['C'].get('value')))
        sample = next(r for r in w.project.records if r.role == 'Sample' and C._finite_percentage(
            ((panel.preview['records'].get(str(r.index)) or {}).get('elements') or {}).get('C', {}).get('value')))
        panel.record = sample; panel.element = 'C'
        value_before = panel.current_result()['value']; slope_before = panel.preview['calibrations']['C']['slope']
        q, ident, point = next(h for h in cal._hits if h[2].get('included', True) and h[2].get('area') is not None)
        QTest.mouseClick(cal, Qt.LeftButton, Qt.NoModifier, QPoint(round(q.x()), round(q.y()))); app.processEvents()
        fit = panel.preview['calibrations']['C']
        excluded = next(p for p in fit['points'] if str(p['id']) == ident)
        row = next(i for i, r in enumerate(kp.rows) if r is not None and str(r.index) == ident)
        check('the list shows the standard as excluded', kp.table.item(row, kp.FIRST + 1).text() == 'excluded')
        check('one click excludes the standard', excluded['included'] is False and ident in fit['excluded_ids'])
        check('curve recalculated without it', not math.isclose(fit['slope'], slope_before, rel_tol=1e-12))
        expected = C.proc_quantify(panel.current_result()['area'], panel.record.weight_mg, fit)['value']
        check('sample result follows the new curve', math.isclose(panel.current_result()['value'], expected, rel_tol=1e-12)
              and not math.isclose(panel.current_result()['value'], value_before, rel_tol=1e-12))
        cal.repaint(); app.processEvents()
        q = next(h[0] for h in cal._hits if h[1] == ident)
        QTest.mouseClick(cal, Qt.LeftButton, Qt.NoModifier, QPoint(round(q.x()), round(q.y()))); app.processEvents()
        fit = panel.preview['calibrations']['C']
        check('second click restores it', next(p for p in fit['points'] if str(p['id']) == ident)['included'] is True
              and math.isclose(fit['slope'], slope_before, rel_tol=1e-12))
        check('restored result equals the original', math.isclose(panel.current_result()['value'], value_before, rel_tol=1e-12))
        kp.undo(); app.processEvents()
        check('undo brings the exclusion back', ident in panel.preview['calibrations']['C']['excluded_ids'])
        # See peak: a standard's peak opens in step 5
        std_row = next(i for i, r in enumerate(kp.rows) if r is not None and r.role == 'Calibration')
        kp.table.setCurrentCell(std_row, kp.FIRST + 2); app.processEvents(); kp.see_peak(); app.processEvents()
        check('See peak opens the standard in step 5', w.currentId() == 5 and panel.record is kp.rows[std_row] and panel.element == 'H',
              (w.currentId(), getattr(panel.record, 'name', None), panel.element))
        # draw a peak where the element has none
        target = None
        for r in w.project.records:
            entry = panel.preview['records'].get(str(r.index))
            if not entry or r.role not in ('Sample', 'Check') or not C._processing_trace(r): continue
            for e in C.ELEMENTS:
                if entry['elements'][e].get('start') is None and not entry['elements'][e].get('reviewed_zero'):
                    target = (r, e); break
            if target: break
        if target:
            panel.show_record(target[0].index, target[1]); app.processEvents()
            plot = panel.plot; plot.reset_view(); app.processEvents()
            panel.draw_button.setChecked(True); app.processEvents()
            check('missing peak can be drawn', plot.can_create and plot.draw_mode and not plot.editable, (target[0].name, target[1], panel.not_editable_reason(), panel.current_result().get('reviewed_zero'), target[0].states.get(target[1])))
            window = panel.preview['windows'][target[1]]; lo_i, hi_i = int(window['start']) + 3, int(window['end']) - 3
            y = round(plot.plot_rectangle().center().y()); a = plot.point_to_screen(lo_i, 0).x(); b = plot.point_to_screen(hi_i, 0).x()
            QTest.mousePress(plot, Qt.LeftButton, Qt.NoModifier, QPoint(round(a), y))
            QTest.mouseMove(plot, QPoint(round(b), y))
            QTest.mouseRelease(plot, Qt.LeftButton, Qt.NoModifier, QPoint(round(b), y)); app.processEvents()
            item = panel.current_result()
            check('dragging across the trace integrates a new peak', item.get('start') is not None and abs(item['start'] - lo_i) <= 2 and abs(item['end'] - hi_i) <= 2,
                  (item.get('start'), item.get('end')))
            check('drawn peak counts as an analyst assignment', item.get('assignment_confirmed') is True)
            check('new peak now has Start/End handles', plot.editable and not plot.can_create)
        else:
            check('no missing peak in this run (draw test skipped)', True)
        # left-drag on empty space pans the chromatogram and the calibration plot
        plot = panel.plot; plot.zoom_to_peak(); app.processEvents(); before = plot.visible_range()
        y = round(plot.plot_rectangle().top() + 40)
        x = next(round(xx) for xx in range(int(plot.plot_rectangle().left()) + 150, int(plot.plot_rectangle().right()) - 20, 5)
                 if plot._handle_at(QPointF(xx, y)) is None and plot._other_handle_at(QPointF(xx, y)) is None)
        step = -120 if before[1] < len(plot.trace['signal']) - 1 else 120  # drag towards the side that has room
        QTest.mousePress(plot, Qt.LeftButton, Qt.NoModifier, QPoint(x, y)); QTest.mouseMove(plot, QPoint(x + step, y))
        QTest.mouseRelease(plot, Qt.LeftButton, Qt.NoModifier, QPoint(x + step, y)); app.processEvents()
        moved = plot.visible_range()[0] - before[0]
        check('left-drag moves the chromatogram view the same way as the mouse', (moved > 0) if step < 0 else (moved < 0), (before, plot.visible_range()))
        w.next(); app.processEvents(); kp.set_element('C'); cal.resize(700, 300)
        cal.repaint(); app.processEvents(); limits = cal.limits(); r = cal.rect()
        empty = QPoint(round(r.left() + 30), round(r.top() + 20))
        QTest.mousePress(cal, Qt.LeftButton, Qt.NoModifier, empty); QTest.mouseMove(cal, QPoint(empty.x() + 80, empty.y()))
        QTest.mouseRelease(cal, Qt.LeftButton, Qt.NoModifier, QPoint(empty.x() + 80, empty.y())); app.processEvents()
        check('left-drag moves the calibration view', cal.limits()[0] < limits[0], (limits, cal.limits()))
        # apply with an excluded standard: its reason is recorded
        panel.apply_to_report(); app.processEvents()
        active = w.project.processing.get('active_preview') or {}
        reasons = [r for items in (active.get('exclusions') or {}).values() for r in items.values()]
        check('apply records the analyst reason for the exclusion', any(r.endswith('test reason') for r in reasons), reasons)
    except Exception:
        traceback.print_exc(); results.append(False)
    print(f'{sum(results)} passed, {len(results) - sum(results)} failed'); os._exit(0 if all(results) else 1)
orig = QApplication.exec
QApplication.exec = lambda *a: (QTimer.singleShot(200, go), orig())[1]
C.launch_gui()
