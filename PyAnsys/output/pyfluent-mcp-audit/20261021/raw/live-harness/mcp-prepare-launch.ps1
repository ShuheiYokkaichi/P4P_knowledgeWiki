$r='C:\Users\syok443\Documents\FluentRuns\MCPContribution\20261021'
Get-ChildItem Env: | Where-Object {$_.Name -match '^(FLUENT_|FL_|PYTHONHOME$|PYTHONPATH$)'} | ForEach-Object {Remove-Item ('Env:'+ $_.Name)}
$env:AWP_ROOT252='C:\Program Files\ANSYS Inc\v252'
& "$r\runtime\Scripts\python.exe" "$r\mcp-prepare-cases.py" 1> "$r\prepare.stdout.txt" 2> "$r\prepare.stderr.txt"
