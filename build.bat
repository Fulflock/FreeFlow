@echo off
setlocal
title FreeFlow Build
cd /d "%~dp0"

echo === [1/6] Verifying Python 3.12 ===
py -3.12 --version || (echo Python 3.12 introuvable. Installe-le depuis python.org. & pause & exit /b 1)

echo === [2/6] Creating / activating venv ===
if not exist ".venv\Scripts\python.exe" (
    py -3.12 -m venv .venv || (echo venv creation failed & pause & exit /b 1)
)
call .venv\Scripts\activate.bat

echo === [3/6] Upgrading pip ===
python -m pip install --upgrade pip wheel setuptools

echo === [4/6] Installing dependencies ===
python -m pip install -r requirements.txt
python -m pip install keyboard pywin32 pyinstaller Pillow

echo === [5/6] Generating icon if missing ===
if not exist "assets\freeflow.ico" (
    python scripts\generate_icon.py || (echo Icon generation failed & pause & exit /b 1)
)

echo === [6/6] Running PyInstaller ===
python -m PyInstaller --noconfirm --clean FreeFlow.spec || (echo Build failed & pause & exit /b 1)

if not exist "dist\FreeFlow.exe" (
    echo ERROR: dist\FreeFlow.exe not produced.
    pause & exit /b 1
)

echo.
echo ============================================================
echo  Build OK -^> dist\FreeFlow.exe
echo  Next: double-click install.cmd to create the desktop shortcut
echo ============================================================
pause
endlocal
