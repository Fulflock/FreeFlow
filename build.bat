@echo off
title WhisperFlow Build
cd /d "%~dp0"

echo Installation de PyInstaller...
py -3.12 -m pip install pyinstaller

echo.
echo Build de WhisperFlow.exe...
py -3.12 -m PyInstaller ^
    --onedir ^
    --noconsole ^
    --name WhisperFlow ^
    --add-data "config.json;." ^
    --hidden-import faster_whisper ^
    --hidden-import ctranslate2 ^
    --hidden-import onnxruntime ^
    --hidden-import sounddevice ^
    --hidden-import _sounddevice_data ^
    --hidden-import pynput ^
    --hidden-import pynput.keyboard._win32 ^
    --hidden-import pynput.mouse._win32 ^
    --hidden-import pystray ^
    --hidden-import pystray._win32 ^
    --hidden-import pyperclip ^
    --hidden-import PIL ^
    --hidden-import tokenizers ^
    --hidden-import huggingface_hub ^
    --collect-all faster_whisper ^
    --collect-all ctranslate2 ^
    --collect-all sounddevice ^
    --collect-all onnxruntime ^
    src/main.py

echo.
echo Copie du config.json a cote de l'exe...
copy config.json dist\WhisperFlow\config.json

echo.
echo Build termine ! L'exe est dans dist\WhisperFlow\WhisperFlow.exe
pause
