"""Execute visually reviewed plans by copying; never delete originals."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''): h.update(block)
    return h.hexdigest()

def inside(root,name):
    rel=Path(name)
    if rel.is_absolute() or '..' in rel.parts or not rel.parts: raise ValueError('Unsafe path')
    p=(root/rel).resolve()
    if p==root or not p.is_relative_to(root): raise ValueError('Path escapes root')
    return p

def copy(src,dst,sha):
    dst.parent.mkdir(parents=True,exist_ok=True)
    with src.open('rb') as a,dst.open('xb') as b: shutil.copyfileobj(a,b)
    if digest(dst)!=sha: raise ValueError('Copy checksum mismatch')
    shutil.copystat(src,dst)

def apply(source,plan,output):
    source=Path(source).resolve(); output=Path(output).resolve()
    if not source.is_dir() or output.exists() or output.is_relative_to(source): raise ValueError('Use a new output outside source')
    jobs=[]; seen=set(); ids=set()
    for g in json.loads(Path(plan).read_text(encoding='utf-8'))['groups']:
        if g['id'] in ids or g['keeper'] not in g['files'] or not g['reason'].strip(): raise ValueError('Invalid group')
        ids.add(g['id'])
        for name in g['files']:
            src=inside(source,name)
            if src in seen or not src.is_file(): raise ValueError('Duplicate or missing input')
            seen.add(src)
            relative=str(Path('highlights' if name==g['keeper'] else 'memories')/name)
            dst=inside(output,relative)
            row=dict(file=name,source=str(src),destination=relative,sha256=digest(src),group=g['id'],reason=g['reason'])
            jobs.append((src,dst,row))
    if not jobs: raise ValueError('Empty plan')
    output.mkdir(parents=True,exist_ok=False)
    with (output/'manifest.jsonl').open('x',encoding='utf-8') as log:
        for src,dst,row in jobs:
            log.write(json.dumps(dict(row,status='planned'),ensure_ascii=False)+'\n'); log.flush(); os.fsync(log.fileno())
            copy(src,dst,row['sha256'])
            log.write(json.dumps(dict(row,status='copied'),ensure_ascii=False)+'\n'); log.flush(); os.fsync(log.fileno())
    return len(jobs)

def restore(album,name,output):
    album=Path(album).resolve(); output=Path(output).resolve()
    if output.exists() or output.is_relative_to(album): raise ValueError('Use new restore directory')
    rows=[json.loads(s) for s in (album/'manifest.jsonl').read_text(encoding='utf-8').splitlines()]
    r=next(r for r in reversed(rows) if r['file']==name and r['status']=='copied')
    src=inside(album,r['destination']); dst=inside(output,name)
    if digest(src)!=r['sha256']: raise ValueError('Archive changed')
    copy(src,dst,r['sha256'])
    return str(dst)

if __name__=='__main__':
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('apply'); r=sub.add_parser('restore')
    for f in ('source','plan','output'): a.add_argument('--'+f,required=True)
    for f in ('album','file','output'): r.add_argument('--'+f,required=True)
    x=p.parse_args()
    print(apply(x.source,x.plan,x.output) if x.cmd=='apply' else restore(x.album,x.file,x.output))
