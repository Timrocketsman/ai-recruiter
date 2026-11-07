#!/usr/bin/env python3
"""Export an exact public-file manifest; dry review is not content or release acceptance. No model, key, network or publication."""
from pathlib import Path, PurePosixPath
import hashlib,json,os,re,shutil,stat,subprocess,sys
MAX_PUBLIC_BYTES=160000000
PUBLIC_SUFFIXES={'.html','.css','.js','.json','.xml','.txt','.jpg','.jpeg','.png','.webp','.svg','.ico','.woff','.woff2','.mp4','.webm','.avif','.pdf','.m4a','.mp3','.webmanifest'}
DENIED_FILES={'SESSIONS.md','data/content_plan.json','data/channel_audit_20261019.json'}
DENIED={'.git','.github','.env','.ssh','knowledge','secrets','private','runtime','agent_profile','node_modules','tools','scripts','templates','tests'}
def strict_json(raw):
 def pairs(items):
  d={}
  for k,v in items:
   if k in d:raise ValueError('duplicate JSON key')
   d[k]=v
  return d
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def export(source,manifest,expected_sha,expected_manifest_sha,out,publish_requested=False):
 source=Path(source);manifest=Path(manifest);out=Path(out)
 if not re.fullmatch('[0-9a-f]{40}',expected_sha) or not re.fullmatch('[0-9a-f]{64}',expected_manifest_sha):raise ValueError('invalid exact identity')
 raw=manifest.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=expected_manifest_sha:raise ValueError('manifest changed')
 d=strict_json(raw)
 if type(d)is not dict or set(d)!={'schema','repository','commit','root_review_ref','files'} or d['schema']!='timlabs_reviewed_public_pages_v1' or d['repository']!='Timrocketsman/ai-recruiter' or d['commit']!=expected_sha:raise ValueError('closed release identity')
 if type(d['root_review_ref'])is not str or not 3<=len(d['root_review_ref'])<=200:raise ValueError('missing public ROOT review reference')
 if type(publish_requested)is not bool:raise ValueError('invalid publication request type')
 if publish_requested and d['root_review_ref'].startswith('DRY_EXPORT_REVIEW_ONLY'):raise ValueError('dry export manifest cannot authorize publication')
 files=d['files']
 if type(files)is not dict or not files or len(files)>20000 or 'index.html' not in files or files.get('CNAME') not in {hashlib.sha256(b'timlabs.online').hexdigest(),hashlib.sha256(b'timlabs.online\n').hexdigest()}:raise ValueError('public index/domain required')
 head=subprocess.run(['git','-C',str(source),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
 if head!=expected_sha:raise ValueError('checkout drift')
 validated=[];total=0
 for name,h in files.items():
  if type(name)is not str or type(h)is not str or not re.fullmatch('[0-9a-f]{64}',h):raise ValueError('invalid manifest entry')
  p=PurePosixPath(name)
  if name!='CNAME' and p.suffix.lower() not in PUBLIC_SUFFIXES:raise ValueError('not a reviewed browser asset type')
  if name in DENIED_FILES or p.is_absolute() or str(p)!=name or any(x in ('..','.') or x in DENIED or x.startswith('.') or x.endswith(('.key','.pem')) for x in p.parts):raise ValueError('private or unsafe path')
  path=source/name
  for parent in (path,*path.parents):
   if parent==source.parent:break
   if stat.S_ISLNK(parent.lstat().st_mode):raise ValueError('symlink forbidden')
  st=path.stat()
  if not stat.S_ISREG(st.st_mode) or st.st_nlink!=1:raise ValueError('only regular singlelink public files')
  if st.st_size>MAX_PUBLIC_BYTES-total:raise ValueError('bounded public artifact size exceeded before read')
  rawfile=path.read_bytes();total+=len(rawfile)
  if total>MAX_PUBLIC_BYTES:raise ValueError('bounded public artifact size exceeded')
  if hashlib.sha256(rawfile).hexdigest()!=h:raise ValueError('public bytes changed')
  validated.append((name,rawfile))
 if out.exists():raise ValueError('new output only')
 out.mkdir(parents=True)
 for name,data in validated:
  dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 return {'commit':expected_sha,'manifest_sha256':expected_manifest_sha,'files':len(validated),'bytes':total,'root_review_ref':d['root_review_ref'],'source_legal_gate_not_implemented_in_CI':True,'review_scope':'dry_export_only' if d['root_review_ref'].startswith('DRY_EXPORT_REVIEW_ONLY') else 'external_ROOT_release_review_required'}
if __name__=='__main__':
 if len(sys.argv)!=6:raise SystemExit('source manifest commit manifest_sha output')
 flag=os.environ.get('PUBLISH_REQUESTED','false')
 if flag not in ('true','false'):raise SystemExit('invalid PUBLISH_REQUESTED')
 print(json.dumps(export(*sys.argv[1:],publish_requested=flag=='true'),sort_keys=True))
