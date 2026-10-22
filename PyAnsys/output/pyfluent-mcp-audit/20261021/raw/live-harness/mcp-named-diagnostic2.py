import asyncio,json,os,threading,time,traceback
from pathlib import Path
from ansys.fluent.mcp.solve.backends.pyfluent import PyFluentBackend
from ansys.fluent.mcp.solve.backends import introspection as intro
root=Path(__file__).parent
import logging
intro.logger.setLevel(logging.DEBUG)
intro.logger.addHandler(logging.FileHandler(root/'named-debug.log'))
out={'started':time.time(),'sessions':[]}
def save(): (root/'named-diagnostic2.json').write_text(json.dumps(out,indent=2,ensure_ascii=True,default=str))
def expired():out['timeout']=True;save();os._exit(124)
t=threading.Timer(240,expired);t.daemon=True;t.start()
async def main():
 backends=[PyFluentBackend(),PyFluentBackend()]
 try:
  for b in backends:
   out['stage']='CONNECT';save();await b.connect(ui_mode='no_gui',precision='double')
  for b,name in zip(backends,['mixing_elbow.cas.h5','mixing_elbow_copy.cas.h5']):
   out['stage']='READ';save();b._solver.settings.file.read(file_type='case',file_name=(root/'cases'/name).as_posix(),lightweight_setup=True)
  for i,b in enumerate(backends):
   row={'side':i};out['sessions'].append(row)
   out['stage']='GLOBAL_'+str(i);save();row['global']=await b.get_state()
   row['walk_before_scheme']=intro.discover_named_objects_via_walk(b._solver.settings);save()
   for key,expr in [('silenced',"(let* ((__sink (open-output-string)) (__result (with-output-to-port __sink (lambda () (err-protect (api-get-named-object-names (get flapi-objects root))))))) __result)"),('plain',"(err-protect (api-get-named-object-names (get flapi-objects root)))")]:
    out['stage']=key+'_'+str(i);save()
    try:
     raw=b._solver.scheme.eval(expr)
     row[key]={'type':type(raw).__name__,'repr':repr(raw)[:6000]}
    except Exception:row[key]={'error':traceback.format_exc()}
    save()
   row['root_child_names']=list(b._solver.settings.child_names)
   row['root_indexable']=hasattr(b._solver.settings,'__getitem__')
   row['root_get_object_names']=hasattr(b._solver.settings,'get_object_names')
   out['stage']='DISCOVER_'+str(i);save()
   row['via_scheme']=intro.discover_named_objects_via_scheme(b._solver)
   row['via_walk']=intro.discover_named_objects_via_walk(b._solver.settings)
   save()
  out['stage']='COMPLETED'
 finally:
  for b in backends:await b.disconnect()
try:asyncio.run(main())
except BaseException:out['exception']=traceback.format_exc()
finally:out['finished']=time.time();save();t.cancel()
