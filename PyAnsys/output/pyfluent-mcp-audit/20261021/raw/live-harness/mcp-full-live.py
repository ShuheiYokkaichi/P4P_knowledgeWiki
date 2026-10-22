import asyncio,base64,hashlib,json,os,threading,time,traceback,sys
from pathlib import Path
import psutil
root=Path(__file__).parent
out={'started':time.time(),'acceptance':'NOT_ESTABLISHED'}
def save(): (root/'full-live.json').write_text(json.dumps(out,indent=2,ensure_ascii=True))
def expired():out['timeout']=True;save();os._exit(124)
timer=threading.Timer(600,expired);timer.daemon=True;timer.start()
# Deploy the exact contribution sources before importing either module.
site=Path(sys.prefix)/'Lib/site-packages/ansys/fluent/mcp/solve'
out['sources']={}
for name,target in [('compare_tools_v2.b64',site/'lib/compare_tools.py'),('introspection_v2.b64',site/'backends/introspection.py')]:
 code=base64.b64decode((root/name).read_text());target.write_bytes(code)
 out['sources'][name]=hashlib.sha256(code).hexdigest()
from ansys.fluent.mcp.solve.lib.compare_tools import compare_files_impl
from ansys.fluent.mcp.solve.backends.pyfluent import PyFluentBackend
from ansys.fluent.mcp.solve.backends import introspection as intro
import ansys.fluent.core as pf
out['pyfluent']=pf.__version__
def processes():
 rows=[]
 for p in psutil.process_iter(['pid','name','create_time']):
  if p.info['name'].lower().startswith(('fluent','fl2520','cx2520')): rows.append(p.info)
 return rows
async def run(label,a,b):
 out['stage']=label;save()
 before=processes()
 result=await compare_files_impl(PyFluentBackend(),path_a=str(a),path_b=str(b))
 prior={p['pid'] for p in before}
 deadline=time.monotonic()+45
 while True:
  remaining=[p for p in processes() if p['pid'] not in prior]
  if not remaining or time.monotonic()>=deadline:break
  await asyncio.sleep(1)
 out[label]={'result':result,'processes_before':before,'new_processes_remaining':remaining}
 save()
async def main():
 a=root/'cases/mixing_elbow.cas.h5';same=root/'cases/mixing_elbow_copy.cas.h5';changed=root/'cases/energy_off.cas.h5'
 out['cases']={p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in (a,same,changed)}
 await run('equal_cases',a,same)
 await run('changed_energy',a,changed)
 cap=intro._MAX_STATE_BYTES
 try:
  intro._MAX_STATE_BYTES=1
  await run('size_limit',a,same)
 finally:intro._MAX_STATE_BYTES=cap
 eq=out['equal_cases']['result'];delta=out['changed_energy']['result'];small=out['size_limit']['result']
 out['checks']={
  'equal_cases':eq.get('status')=='ok' and eq.get('diff_count')==0,
  'energy_difference':delta.get('status')=='ok' and any(d.get('path')=='global.setup/models/energy.enabled' and d.get('a') is True and d.get('b') is False for d in delta.get('diffs',[])),
  'size_limit_error':small.get('error')=='comparison incomplete' and all(s in small.get('detail',{}) for s in ['path_a','path_b']) and 'summary' not in small and 'diff_count' not in small,
  'cleanup':all(not out[label]['new_processes_remaining'] for label in ['equal_cases','changed_energy','size_limit'])}
 out['acceptance']='PASSED' if all(out['checks'].values()) else 'FAILED'
 out['stage']='COMPLETED'
try:asyncio.run(main())
except BaseException:out['exception']=traceback.format_exc()
finally:out['finished']=time.time();save();timer.cancel()
