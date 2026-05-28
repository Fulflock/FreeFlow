# install_shortcut.ps1 — Create a FreeFlow desktop shortcut with the FF icon.
$ErrorActionPreference = "Stop"

$Here    = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ExePath = Join-Path $Here "dist\FreeFlow.exe"
$IcoPath = Join-Path $Here "assets\freeflow.ico"

if (-not (Test-Path $ExePath)) {
    Write-Host "ERROR: $ExePath introuvable. Lance d'abord build.bat." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $IcoPath)) {
    Write-Host "WARNING: $IcoPath introuvable, l'icone embarquee de l'exe sera utilisee." -ForegroundColor Yellow
    $IcoPath = $ExePath
}

$Desktop      = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "FreeFlow.lnk"
$WorkDir      = Split-Path $ExePath -Parent

$WScript  = New-Object -ComObject WScript.Shell
$Shortcut = $WScript.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath       = $ExePath
$Shortcut.WorkingDirectory = $WorkDir
$Shortcut.IconLocation     = "$IcoPath,0"
$Shortcut.Description      = "FreeFlow - dictee vocale"
$Shortcut.WindowStyle      = 1
$Shortcut.Save()

Write-Host ""
Write-Host "OK : raccourci cree sur le bureau -> $ShortcutPath" -ForegroundColor Green
Write-Host "Double-clique l'icone FF pour lancer FreeFlow." -ForegroundColor Green
