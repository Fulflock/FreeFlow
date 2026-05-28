@echo off
title FreeFlow - Installation du raccourci
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_shortcut.ps1"
echo.
pause
