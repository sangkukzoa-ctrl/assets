# Read-only Android attachment-route diagnostics. No raw logcat is written.
# Run on a PC with Android platform-tools, one authorized USB-debugging device.
param([string]$Adb = "adb", [string]$Output = "$PSScriptRoot\ImageOrder-attachment-route.txt")
$ErrorActionPreference = "Stop"
if (-not (Get-Command $Adb -ErrorAction SilentlyContinue)) { throw "adb not found. Supply -Adb with the path to adb.exe." }
$state = (& $Adb get-state 2>$null | Out-String).Trim()
if ($state -ne "device") { throw "Connect exactly one authorized Android device." }
function Write-Report([string]$Line) {
    $Line | Add-Content -LiteralPath $Output -Encoding UTF8
    Write-Host $Line
}
Set-Content -LiteralPath $Output -Encoding UTF8 -Value "Image Order read-only attachment route diagnostic"
foreach ($property in @("ro.build.version.release","ro.build.version.sdk","ro.product.manufacturer","ro.product.model")) {
    $value = (& $Adb shell getprop $property | Out-String).Trim()
    Write-Report "$property=$value"
}
$pkg = "com.twobornot.imageorder"
$package = & $Adb shell dumpsys package $pkg
foreach ($line in $package) {
    if ($line -match '^\s*(versionCode=\d+|versionName=[0-9.]+)') { Write-Report $Matches[1] }
}
foreach ($action in @("android.intent.action.GET_CONTENT","android.intent.action.PICK","android.provider.action.PICK_IMAGES","android.intent.action.OPEN_DOCUMENT")) {
    foreach ($mime in @("image/*","*/*")) {
        Write-Report "QUERY $action $mime"
        $lines = & $Adb shell "cmd package query-activities --brief -a $action -t '$mime'" 2>$null
        foreach ($line in $lines) {
            if ($line -match '^\s*([A-Za-z0-9_.]+/[A-Za-z0-9_.$]+)\s*$') { Write-Report ("candidate="+$Matches[1]) }
        }
    }
}
Write-Host ""
Write-Host "1. Open ChatGPT, Chat LLM, then Chrome/Claude on the phone."
Write-Host "2. Tap the usual photo/file attachment button in each, then cancel."
Write-Host "3. Press Ctrl+C on the PC when finished. Send only the generated report."
Write-Host "Output: $Output"
Write-Report "LIVE START (no raw log, no URI or filename)"
& $Adb logcat -T 1 -v brief -s ActivityTaskManager:I ActivityManager:I 2>$null | ForEach-Object {
    $line = [string]$_
    if ($line -match '\bSTART\s+u\d+\s+\{') {
        $fields = @()
        foreach ($key in @("act","typ","cmp","pkg")) {
            if ($line -match ("\b"+$key+'=([A-Za-z0-9_.$/*+-]+)')) {
                $fields += "$key=$($Matches[1])"
            }
        }
        if ($fields.Count -gt 0) {
            Write-Report ((Get-Date -Format "HH:mm:ss") + " START " + ($fields -join " "))
        }
    }
}
