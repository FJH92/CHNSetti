"""Summarize validate_boundaries.py output. Usage: python summarize_validation.py validation.json"""
import json, sys, statistics as st
d = json.load(open(sys.argv[1]))
runs = {k: v for k, v in d.items() if 'error' not in v}
print(len(runs), 'runs evaluated,', len(d) - len(runs), 'errors')
def med(x): return st.median(x) if x else float('nan')
def pct(x, q):
    x = sorted(x); return x[min(len(x) - 1, int(q * len(x)))] if x else float('nan')
rows = {}
for e in 'NCHS':
    print(f'\n{e}')
    print(f"{'basis':10} {'LOO |rec-100| med/p90':>24} {'check |err| pp med (n)':>24} {'repl RSD med/p90 (n)':>24} {'flagged':>10} {'|A/Eager-1| med %':>18}")
    for b in ('eager', 'classical', 'advanced'):
        loo = [v for r in runs.values() for v in r[b][e]['loo_recovery_err']]
        allchk = [v for r in runs.values() for v in r[b][e]['check_error_pp']]
        chk = [v for v in allchk if v < 5]  # > 5 pp: counted separately (failed analysis or failed integration)
        rsd = [v for r in runs.values() for v in r[b][e]['replicate_rsd']]
        rev = [sum(r[b][e]['review'][i] for r in runs.values()) for i in (0, 1)]
        ve = [v for r in runs.values() for v in r[b][e]['vs_eager_rel']]
        rows[(e, b)] = dict(loo=med(loo), loo90=pct(loo, .9), chk=med(chk), nchk=len(chk), rsd=med(rsd), rsd90=pct(rsd, .9),
                            nrsd=len(rsd), flagged=(rev[0] / rev[1] * 100 if rev[1] else None), ve=med(ve))
        print(f"{b:10} {med(loo):11.2f} / {pct(loo,.9):6.2f}     {med(chk):12.3f} ({len(chk):3d})    {med(rsd):8.2f} / {pct(rsd,.9):6.2f} ({len(rsd):3d})"
              f"   {('%5.1f %%' % (rev[0]/rev[1]*100)) if rev[1] else '   —':>9} {med(ve):12.2f}   checks off by >5 pp: {len(allchk)-len(chk)}")
# paired comparison per run: which method gives the smaller check error / replicate RSD
print('\nPaired, per element: runs where advanced is better / worse than classical (LOO median per run; replicate RSD median per run)')
for e in 'NCHS':
    for key in ('loo_recovery_err', 'replicate_rsd', 'check_error_pp'):
        better = worse = 0
        for r in runs.values():
            a = [v for v in r['advanced'][e][key] if key != 'check_error_pp' or v < 5]
            c = [v for v in r['classical'][e][key] if key != 'check_error_pp' or v < 5]
            if a and c:
                if med(a) < med(c) - 1e-9: better += 1
                elif med(a) > med(c) + 1e-9: worse += 1
        print(f'  {e} {key:18} better {better:3d}  worse {worse:3d}')
json.dump({f'{e}|{b}': v for (e, b), v in rows.items()}, open(sys.argv[1].replace('.json', '_summary.json'), 'w'), indent=1)
