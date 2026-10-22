import asyncio,hashlib,json,threading,time,os,traceback
from pathlib import Path
from ansys.fluent.mcp.solve.backends.pyfluent import PyFluentBackend
root=Path(__file__).parent
out={'started':time.time()}
def save(): (root/'case-preparation.json').write_text(json.dumps(out,indent=2,ensure_ascii=True))
def timeout():out['timeout']=True;save();os._exit(124)
t=threading.Timer(240,timeout);t.daemon=True;t.start()
async def main():
 b=PyFluentBackend()
 try:
  out['stage']='CONNECTING';save()
  out['connect']=str(await b.connect(ui_mode='no_gui',precision='double'))
  s=b._solver
  out['stage']='READING';save()
  s.settings.file.read(file_type='case',file_name=(root/'cases'/'mixing_elbow.cas.h5').as_posix(),lightweight_setup=True)
  out['run_calculation']=await b.get_state(paths=['solution/run-calculation'])
  out['energy_before']=s.settings.setup.models.energy.enabled();save()
  s.settings.setup.models.energy.enabled=False
  out['energy_after']=s.settings.setup.models.energy.enabled()
  p=root/'cases'/'energy_off.cas.h5'
  s.settings.file.write_case(file_name=p.as_posix())
  out['changed_case']={'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
  out['stage']='CASES_READY';save()
 finally:
  await b.disconnect();out['cleanup_returned']=True
try:asyncio.run(main())
except BaseException:out['exception']=traceback.format_exc()
finally:out['finished']=time.time();save();t.cancel()
