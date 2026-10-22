import base64,json,sys
from pathlib import Path
from mcp_native import native
s,c=native()
r='C:/Users/syok443/Documents/FluentRuns/MCPContribution/20261021/'
try:
 for name in sys.argv[1:]:
  assert '/' not in name and '\\' not in name and "'" not in name
  code="$b=[Convert]::ToBase64String([IO.File]::ReadAllBytes('"+r+name+"'));[IO.File]::WriteAllText('"+r+"fetch.scm','\"'+$b+'\"',[Text.Encoding]::ASCII)"
  enc=base64.b64encode(code.encode('utf-16le')).decode()
  s.scheme.eval('(system "cmd /c powershell -NoProfile -EncodedCommand '+enc+'")')
  raw=s.scheme.eval('(with-input-from-file "'+r+'fetch.scm" read)')
  b=base64.b64decode(raw)
  Path('PyAnsys/output/pyfluent-mcp-audit/20261021',name).write_bytes(b)
  print('saved',name,len(b))
finally:c.close()
