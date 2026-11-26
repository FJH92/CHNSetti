"""CHNSetti 1.0.0 display: round markers instead of Start/End lines, labels in % w/w, peak area as
'2.78 × 10⁶', calibration box in words, keyboard zoom (no middle mouse button needed).
Usage: python test_display_100.py src/chnsetti.py RUN.MTH"""
import os, sys, math, traceback, importlib.util
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
s = importlib.util.spec_from_file_location('c', sys.argv[1]); C = importlib.util.module_from_spec(s); sys.modules['c'] = C; s.loader.exec_module(C)
from PySide6.QtWidgets import QApplication, QMessageBox, QWizard, QDialog, QLineEdit
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
QMessageBox.exec = lambda self: 0
QDialog.exec = lambda self: QDialog.Accepted
results = []
def check(name, ok, detail=''):
    results.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + ('' if ok or not detail else ' — ' + str(detail)), flush=True)

# ---- number formats (no GUI)
check('area 2 783 518 → 2.78 × 10⁶', C.format_area(2783518) == '2.78 × 10⁶', C.format_area(2783518))
check('area 221 000 → 2.21 × 10⁵', C.format_area(221000) == '2.21 × 10⁵', C.format_area(221000))
check('small area plain', C.format_area(512.4) == '512', C.format_area(512.4))
check('missing area is a dash', C.format_area(None) == '—' and C.format_area(float('nan')) == '—')
check('K 4 579 617 → 4.580 × 10⁶', C.format_factor(4579617) == '4.580 × 10⁶', C.format_factor(4579617))
fit = {'slope': 4579617.0, 'intercept': 0.0, 'r_squared': 0.99991,
       'points': [{'area': 1, 'recovery_pct': 98.9, 'included': True}, {'area': 1, 'recovery_pct': 100.6, 'included': True},
                  {'area': 1, 'recovery_pct': 100.1, 'included': True}, {'area': 1, 'recovery_pct': 80.0, 'included': False}]}
lines = C.calibration_lines(fit, 'C')
check('calibration in words', lines == ['Carbon: peak area = K × carbon mass', 'K = 4.580 × 10⁶ per mg',
                                        '3 standards  ·  recoveries 98.9 – 100.6 %'], lines)
check('excluded standard not counted', lines[2].startswith('3 standards'))
check('no curve → no lines', C.calibration_lines({'slope': None}, 'C') == [])
with_b = C.calibration_lines(dict(fit, intercept=-1200.0), 'N')
check('intercept named b when used', with_b[0].endswith('+ b') and 'b = ' in with_b[1], with_b)

def colour_close(a, b, tol=40):
    return abs(a.red() - b.red()) + abs(a.green() - b.green()) + abs(a.blue() - b.blue()) <= tol

def go():
    try:
        app = QApplication.instance(); w = [x for x in app.topLevelWidgets() if isinstance(x, QWizard)][0]; w.resize(1400, 950)
        w.next(); w.pages[1].import_selected_file(sys.argv[2]); app.processEvents()
        while w.currentId() < 5: w.next(); app.processEvents()
        cp = w.pages[5]; panel = cp.panel; plot = panel.plot
        rec = next(r for r in w.project.records if r.role == 'Sample' and C._processing_trace(r)
                   and (C._processing_trace(r).get('channels', {}).get('H') or {}).get('present'))
        cp.focus_measurement(rec.index, 'H'); app.processEvents()
        plot.reset_view(); app.processEvents()
        image = plot.grab().toImage(); ratio = image.devicePixelRatio() or 1
        res = panel.current_result(); colour = QColor(C.FIGURE_COLORS['H']) if hasattr(C, 'FIGURE_COLORS') else None
        start = plot.point_to_screen(res['start'], plot.trace_value(res['start']))
        px = lambda x, y: image.pixelColor(int(x * ratio), int(y * ratio))
        centre = px(start.x(), start.y())
        check('filled marker on the curve at Start', colour is None or colour_close(centre, colour, 90), centre.name())
        rect = plot.plot_rectangle()
        column = [px(start.x(), y) for y in range(int(rect.top()) + 30, int(start.y()) - 25)]
        ys = [y for y, c in zip(range(int(rect.top()) + 30, int(start.y()) - 25), column) if colour is not None and colour_close(c, colour, 90)]
        # a Start line would colour most of the column; a peak label crossing it colours only its own rows
        check('no vertical Start line above the marker', len(ys) < len(column) * 0.15, f'{len(ys)} rows of {len(column)}')
        check('hint tells to drag the round markers', 'round markers' in plot.hint, plot.hint)
        txt = panel.result_label.text()
        check('sample line: element in this portion, % w/w, peak area in detector units',
              'Hydrogen in this portion:' in txt and '% w/w' in txt and '(detector units)' in txt, txt)
        # ---- keyboard zoom (no middle button needed)
        plot.setFocus(); app.processEvents()
        lo0, hi0 = plot.view_window()
        QTest.keyClick(plot, Qt.Key_Plus); app.processEvents()
        lo1, hi1 = plot.view_window()
        check('+ zooms in on the time axis', (hi1 - lo1) < (hi0 - lo0) * 0.9, (lo0, hi0, lo1, hi1))
        QTest.keyClick(plot, Qt.Key_Minus); QTest.keyClick(plot, Qt.Key_Minus); app.processEvents()
        lo2, hi2 = plot.view_window()
        check('− zooms out', (hi2 - lo2) > (hi1 - lo1), (lo1, hi1, lo2, hi2))
        _, _, y0, y1 = plot.data_limits()
        QTest.keyClick(plot, Qt.Key_Up); app.processEvents()
        _, _, y2, y3 = plot.data_limits()
        check('↑ zooms the signal axis', (y3 - y2) < (y1 - y0) * 0.9, (y0, y1, y2, y3))
        QTest.keyClick(plot, Qt.Key_Down); QTest.keyClick(plot, Qt.Key_Down); app.processEvents()
        _, _, y4, y5 = plot.data_limits()
        check('↓ zooms the signal axis out', (y5 - y4) > (y3 - y2), (y2, y3, y4, y5))
        QTest.keyClick(plot, Qt.Key_0); app.processEvents()
        check('0 shows everything again', plot._range is None and getattr(plot, '_yrange', None) is None)
        before = dict(panel.current_result())
        QTest.keyClick(plot, Qt.Key_Plus); QTest.keyClick(plot, Qt.Key_Up); QTest.keyClick(plot, Qt.Key_0); app.processEvents()
        check('zoom keys never move a boundary', panel.current_result()['start'] == before['start'] and panel.current_result()['end'] == before['end'])
        # ---- step 4 (calibration, before the chromatograms)
        w.back(); app.processEvents()
        kp = w.pages[4]; curve = kp.curve
        check('step 4 is the calibration, step 5 the chromatograms', w.currentPage() is kp and w.steps.TITLES[3:5] == ('Calibration', 'Chromatograms'))
        kp.set_element('C'); app.processEvents()
        has_check = any(r.role == 'Check' for r in w.project.records)
        if has_check:
            box = curve.check_lines()
            check('check-material box: just the result and the certificate', box and all(('certificate' in line) == (line.count('%') == 2) for line in box)
                  and not any(word in ' '.join(box) for word in ('off by', 'before', 'closer', 'further')), box)
            expected = C.DEMO_REFERENCE_NAME if w.project.demo else C.default_check_reference(w.project)
            check('the batch dated on or before the run is proposed (the theoretical composition for the demonstration)',
                  w.project.settings.reference_table == expected)
            check('certified values chooser shows that batch', kp.cert_combo.isVisible() and kp.cert_combo.currentText() == w.project.settings.reference_table)
            checks_now = C.check_material_results(w.project, kp.preview(), 'C')
            found = [r for r in checks_now if r['found'] is not None and r['certified'] is not None]
            if found:
                check('box line: result and certificate', any(f"{found[0]['found']:.2f} %" in line and f"certificate {found[0]['certified']:.2f} %" in line for line in box), box)
                pts = [pt for pt in kp.preview()['calibrations']['C']['points'] if pt.get('included', True) and pt.get('area') is not None]
                kp.toggle_point(pts[0]['id'], True); app.processEvents()
                after = C.check_material_results(w.project, kp.preview(), 'C')[0]
                check('the box follows an exclusion at once', not math.isclose(after['found'], found[0]['found'], rel_tol=1e-12)
                      and any(f"{after['found']:.2f} %" in line for line in curve.check_lines()), curve.check_lines())
                kp.undo(); app.processEvents()
            other = next(n for n in C.REFERENCES if n not in (w.project.settings.reference_table, C.NO_REFERENCE))
            kp.choose_certificate(other); app.processEvents()
            cert_other = (C.REFERENCES[other].get(C.check_material(next(r for r in w.project.records if r.role == 'Check').name)) or {}).get('C')
            check('choosing another batch changes the certified value', w.project.settings.reference_table == other and
                  (cert_other is None or any(f'certificate {cert_other:.2f} %' in line for line in curve.check_lines()) or
                   not any('%' in line for line in curve.check_lines())), curve.check_lines())
            kp.choose_certificate(C.default_check_reference(w.project)); app.processEvents()
        lines = curve.equation_lines()
        check('calibration box first line', lines and lines[0] == 'Carbon: peak area = K × carbon mass', lines)
        check('R² only in the tooltip', all('R²' not in l for l in lines) and 'R²' in curve.equation_tooltip())
        std = next(pt for pt in curve.fit.get('points') or [] if pt.get('area') is not None)
        curve.selected_id = std.get('id'); curve.repaint(); app.processEvents()
        tags = curve.axis_tag_texts()
        amount = next(x for x, y, pt in curve.points() if pt is std)
        check('dashed lines of the selected standard end in axis values (mg, peak area)',
              len(tags) == 1 and tags[0][0] == f'{amount:.4f} mg' and tags[0][1] == C.format_area(std['area']), tags)
        curve.selected_id = None; curve.repaint(); app.processEvents()
        check('no tags without a selection', curve.axis_tag_texts() == [] or curve.sample is not None, curve.axis_tag_texts())
        curve.setFocus(); app.processEvents()
        x0, x1, _, _ = curve.limits()
        QTest.keyClick(curve, Qt.Key_Plus); app.processEvents()
        a0, a1, _, _ = curve.limits()
        check('+ zooms the calibration curve', (a1 - a0) < (x1 - x0) * 0.9, (x0, x1, a0, a1))
        QTest.keyClick(curve, Qt.Key_0); app.processEvents()
        check('0 resets the calibration view', curve._range is None)
    except Exception:
        traceback.print_exc(); results.append(False)
    print(f'{sum(results)} passed, {results.count(False)} failed', flush=True); os._exit(0 if all(results) else 1)

orig = QApplication.exec
QApplication.exec = lambda *a: (QTimer.singleShot(200, go), orig())[1]
C.launch_gui()
