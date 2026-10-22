import sys,base64,hashlib
from pathlib import Path
from mcp_native import native
from pyansys_fluent.remote_text import ascii_write_expression
s,c=native();r='C:/Users/syok443/Documents/FluentRuns/MCPContribution/20261021/'
try:
 for name in sys.argv[1:]:
  p=Path(name);target=r+p.name;t=p.read_text()
  if s.scheme.eval('(file-exists? "'+target+'")'):raise FileExistsError(target)
  s.scheme.eval(ascii_write_expression(target,t))
  expected=hashlib.sha256(t.replace('\n','\r\n').encode()).hexdigest().upper()
  code="$h=(Get-FileHash '"+target+"').Hash;[IO.File]::WriteAllText('"+r+"hash.scm','\"'+$h+'\"',[Text.Encoding]::ASCII)"
  enc=base64.b64encode(code.encode('utf-16le')).decode()
  s.scheme.eval('(system "cmd /c powershell -NoProfile -EncodedCommand '+enc+'")')
  actual=s.scheme.eval('(with-input-from-file "'+r+'hash.scm" read)')
  if actual!=expected:raise ValueError('host file hash mismatch')
  print('verified',p.name)
finally:c.close()
