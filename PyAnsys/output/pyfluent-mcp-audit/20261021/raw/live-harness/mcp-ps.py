import sys,base64,json
from mcp_native import native
s,c=native()
r='C:/Users/syok443/Documents/FluentRuns/MCPContribution/20261021/'
code=sys.stdin.read()+"\n$j=$o|ConvertTo-Json -Depth 5 -Compress; $b=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($j)); [IO.File]::WriteAllText('"+r+"reply.scm','\"'+$b+'\"',[Text.Encoding]::ASCII)"
enc=base64.b64encode(code.encode('utf-16le')).decode()
try:
 print('exit',s.scheme.eval('(system "cmd /c powershell -NoProfile -EncodedCommand '+enc+'")'))
 raw=s.scheme.eval('(with-input-from-file "'+r+'reply.scm" read)')
 print(base64.b64decode(raw).decode())
finally:c.close()
