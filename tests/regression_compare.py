"""Compare every export of two CHNSetti versions over an archive of runs.

Usage: python regression_compare.py OLD.py NEW.py ARCHIVE_FOLDER [part parts]
Timestamps differ between runs; every other cell is compared.
"""
import sys, os, re, json, importlib.util, tempfile, glob, traceback
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
old=load(sys.argv[1],'old');new=load(sys.argv[2],'new')
from openpyxl import load_workbook
def cells(path):
    wb=load_workbook(path,data_only=False);out={}
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                v=c.value
                if v is None:continue
                if isinstance(v,str) and ('UTC' in v or '/tmp' in v or 'chnsetti_' in v):continue
                if isinstance(v,str):  # version numbers and creation times differ by design
                    v=re.sub(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?(\+00:00|Z)?','<time>',v)
                    v=re.sub(r'\b\d+\.\d+\.\d+\b','<version>',v)
                out[(ws.title,c.coordinate)]=v
    return out
runs=sorted({str(p) for p in __import__('pathlib').Path(sys.argv[3]).rglob('*') if p.suffix.lower()=='.mth'})
part,n=(int(sys.argv[4]),int(sys.argv[5])) if len(sys.argv)>5 else (0,1);runs=runs[part::n]
summary={'runs':0,'identical':0,'diff':[],'errors':[]}
for run in runs:
    try:
        res=[]
        for m in (old,new):
            tmp=tempfile.mkdtemp()
            p=m.import_file(run);m.set_settings(p,expected_replicates=3)
            paths=m.export_analysis(p,tmp)
            res.append({k:cells(v) for k,v in paths.items() if str(v).endswith('.xlsx')})
            res[-1]['_preview']=m.preview_native_processing(p)['summary']
        summary['runs']+=1
        a,b=res
        diffs=[]
        for key in a:
            if key=='_preview':
                if a[key]!=b[key]:diffs.append('preview summary')
                continue
            ka={k:v for k,v in a[key].items()};kb=b.get(key,{})
            d=[k for k in set(ka)|set(kb) if ka.get(k)!=kb.get(k)]
            if d:diffs.append((key,len(d),sorted(d)[:3],[ (ka.get(x),kb.get(x)) for x in sorted(d)[:2]]))
        if diffs:summary['diff'].append((run,diffs))
        else:summary['identical']+=1
    except Exception as exc:
        summary['errors'].append((run,repr(exc)[:200]))
json.dump(summary,open(f'regression_part{part}.json','w'),default=str,indent=1)
print(part,'done',summary['runs'],summary['identical'],len(summary['diff']),len(summary['errors']))
