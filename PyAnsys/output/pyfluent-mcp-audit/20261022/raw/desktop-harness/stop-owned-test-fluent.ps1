$root = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq 'fluent.exe' -and
    $_.CommandLine -like '"C:\Program Files\ANSYS Inc\ANSYS Student\v252\fluent\ntbin\win64\fluent.exe"*'
})
if ($root.Count -ne 1) { throw 'BLOCKED: exact pinned Fluent root was not uniquely identified.' }
$all = @(Get-CimInstance Win32_Process)
$ids = [System.Collections.Generic.HashSet[int]]::new()
[void]$ids.Add([int]$root[0].ProcessId)
$changed = $true
while ($changed) {
    $changed = $false
    foreach ($p in $all) {
        if ($ids.Contains([int]$p.ParentProcessId) -and -not $ids.Contains([int]$p.ProcessId)) {
            [void]$ids.Add([int]$p.ProcessId)
            $changed = $true
        }
    }
}
foreach ($p in ($all | Where-Object { $ids.Contains([int]$_.ProcessId) } | Sort-Object { [int]$_.ProcessId } -Descending)) {
    Stop-Process -Id ([int]$p.ProcessId) -Force
}
Start-Sleep -Seconds 2
if (Get-CimInstance Win32_Process | Where-Object { $ids.Contains([int]$_.ProcessId) }) {
    throw 'FAILED: a pinned Fluent process remains.'
}
