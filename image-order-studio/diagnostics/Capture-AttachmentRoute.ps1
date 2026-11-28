# Read-only first-photo-picker diagnostics. No raw logcat or media contents are saved.
param([string]$Adb="",[string]$Output="$PSScriptRoot\ImageOrder-attachment-route.txt",[switch]$SelfTest)
$ErrorActionPreference="Stop"
$componentPattern='[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+/[A-Za-z0-9_.$]+'
$pickerActions=@("android.intent.action.GET_CONTENT","android.intent.action.PICK","android.provider.action.PICK_IMAGES","android.intent.action.OPEN_DOCUMENT","androidx.activity.result.contract.action.PICK_IMAGES","android.intent.action.CHOOSER")
function Get-StartFields([string]$Line) {
    if($Line -notmatch '\bSTART\s+u\d+\s+\{') { return }
    $fields=@{}
    foreach($key in @("act","typ","cmp","pkg")){
        $m=[regex]::Match($Line,"(?:\s|\{)"+$key+'=([A-Za-z0-9_.$/*+-]+)(?=\s|\}|$)')
        if($m.Success){$fields[$key]=$m.Groups[1].Value}
    }
    if(-not ($pickerActions -contains $fields["act"]) -and
        $fields["cmp"] -notmatch '(?i)photopicker|providers\.media|documentsui|gallery|imageorder|intentresolver'){
        return
    }
    $safe=@()
    foreach($key in @("act","typ","cmp","pkg")){if($fields.ContainsKey($key)){$safe+=("$key="+$fields[$key])}}
    if($safe.Count){return ($safe -join " ")}
}
function Get-ResumedComponents([string[]]$Lines){
    foreach($line in $Lines){
        if($line -match '(?:topResumedActivity|mResumedActivity|ResumedActivity)[:=].*?\bu\d+\s+('+$componentPattern+')'){
            $Matches[1]
        }
    }
}
if($SelfTest){
    $sample='I ActivityTaskManager: START u0 {act=android.provider.action.PICK_IMAGES typ=image/* dat=content://private/photo.jpg cmp=com.google.android.providers.media.module/.PhotoPickerActivity (has extras)}'
    $safe=Get-StartFields $sample
    if($safe -ne 'act=android.provider.action.PICK_IMAGES typ=image/* cmp=com.google.android.providers.media.module/.PhotoPickerActivity'){throw "START parser test failed"}
    if(Get-StartFields 'START u0 {act=android.intent.action.VIEW dat=https://private.example cmp=com.other.app/.SecretActivity}'){throw "Unrelated activity filter failed"}
    if((@(Get-ResumedComponents @('  topResumedActivity=ActivityRecord{123 u0 com.android.documentsui/.picker.PickActivity t12}')))[0] -ne 'com.android.documentsui/.picker.PickActivity'){throw "Resumed component parser test failed"}
    Write-Host "PASS: action / MIME / component allowlist, URI and unrelated activity exclusion"
    exit 0
}
if(-not $Adb){
    $candidates=@("$PSScriptRoot\platform-tools\adb.exe","$PSScriptRoot\adb.exe")
    if($env:LOCALAPPDATA){$candidates+=("$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe")}
    $Adb=$candidates | Where-Object {Test-Path -LiteralPath $_ -PathType Leaf} | Select-Object -First 1
    if(-not $Adb){$Adb="adb"}
}
if(-not (Get-Command $Adb -ErrorAction SilentlyContinue)){throw "adb not found. Extract Google's official platform-tools next to this script, or supply -Adb."}
$deviceRows=@(& $Adb devices | Where-Object {$_ -match '^\S+\s+(device|unauthorized|offline)\s*$'})
if($deviceRows.Count -ne 1 -or $deviceRows[0] -notmatch '\sdevice\s*$'){throw "Connect exactly one authorized Android device. No device settings are changed by this script."}
function Write-Report([string]$Line){
    Add-Content -LiteralPath $Output -Encoding UTF8 -Value $Line
    Write-Host $Line
}
Set-Content -LiteralPath $Output -Encoding UTF8 -Value "Image Order first-picker route diagnostic v2"
foreach($property in @("ro.build.version.release","ro.build.version.sdk","ro.product.manufacturer","ro.product.model","ro.build.version.extensions.r","ro.build.version.extensions.s","ro.build.version.extensions.t")){
    $value=(& $Adb shell getprop $property | Out-String).Trim()
    if($value -match '^[A-Za-z0-9_. +()-]{1,100}$'){Write-Report "$property=$value"}
}
$package=& $Adb shell dumpsys package com.twobornot.imageorder
foreach($line in $package){
    if($line -match '^\s*(versionCode=\d+|versionName=[0-9.]+)'){Write-Report $Matches[1]}
}
foreach($action in @("android.intent.action.GET_CONTENT","android.intent.action.PICK","android.provider.action.PICK_IMAGES","android.intent.action.OPEN_DOCUMENT")){
    Write-Report "RESOLVE $action image/*"
    foreach($mode in @("query-activities","resolve-activity")){
        $lines=@(& $Adb shell "cmd package $mode --brief -a $action -t 'image/*'")
        foreach($line in $lines){
            if($line -match "^\s*($componentPattern)\s*$"){Write-Report "$mode $($Matches[1])"}
            elseif($line -match '^\s*priority=(-?\d+)'){Write-Report "$mode priority=$($Matches[1])"}
            elseif($line -match 'No activities found|No activity found'){Write-Report "$mode none"}
        }
    }
}
Write-Host ""
Write-Host "For each case: open the app, but DO NOT open its attachment picker yet."
Write-Host "Press Enter here, tap the normal photo-attachment button on the phone, then leave the FIRST picker visible."
Write-Host "No photo needs to be selected or uploaded. Type s to skip an unavailable app."
foreach($label in @("ChatGPT","Chat LLM","Naver review")){
    $answer=Read-Host "[$label] App ready? Enter / s"
    if($answer -eq "s"){Write-Report "CASE $label SKIPPED";continue}
    Write-Report "CASE $label BEGIN"
    foreach($c in @(Get-ResumedComponents @(& $Adb shell dumpsys activity activities) | Select-Object -Unique)){Write-Report "before=$c"}
    $start=(& $Adb shell "date '+%m-%d %H:%M:%S.000'" | Out-String).Trim()
    if($start -notmatch '^\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}$'){throw "Device timestamp unavailable; no log history will be collected."}
    $answer=Read-Host "Tap attachment on phone, leave first picker visible; press Enter (or s)"
    if($answer -eq "s"){Write-Report "CASE $label SKIPPED";continue}
    $found=@(Get-ResumedComponents @(& $Adb shell dumpsys activity activities) | Select-Object -Unique)
    foreach($c in $found){Write-Report "picker=$c"}
    if(-not $found.Count){Write-Report "picker=unknown"}
    $count=0
    & $Adb logcat -d -T $start -v brief -s ActivityTaskManager:I ActivityManager:I | ForEach-Object {
        $safe=Get-StartFields ([string]$_)
        if($safe){Write-Report "START $safe";$count++}
    }
    Write-Report "matchedStarts=$count"
    Write-Report "CASE $label END"
    Write-Host "Close this picker before moving to the next app."
}
Write-Host ""
Write-Host "Finished. Send only this report: $Output"
