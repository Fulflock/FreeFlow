# -*- mode: python ; coding: utf-8 -*-
# FreeFlow.spec — one-file, windowed, icon-embedded build for Windows
from PyInstaller.utils.hooks import collect_all, collect_submodules
import os

block_cipher = None
APP_NAME = "FreeFlow"
ICON = os.path.abspath("assets/freeflow.ico")

hiddenimports = [
    "faster_whisper", "ctranslate2", "onnxruntime",
    "sounddevice", "_sounddevice_data",
    "pynput", "pynput.keyboard._win32", "pynput.mouse._win32",
    "pystray", "pystray._win32",
    "pyperclip", "tokenizers", "huggingface_hub",
    "PIL", "PIL._tkinter_finder", "PIL.Image", "PIL.ImageDraw", "PIL.ImageFont",
    "tkinter", "tkinter.ttk", "tkinter.filedialog", "tkinter.messagebox",
    "webview", "webview.platforms.edgechromium",
    "keyboard", "win32event", "win32api", "win32con", "win32gui",
    "ctypes", "ctypes.wintypes",
    "src.audio", "src.transcriber", "src.injector", "src.ui",
    "src.history", "src.idle_bubble", "src.main", "src.fonts", "src.updater",
    "src.assets",
    "src.windows", "src.windows.history",
    "src.windows.main_window",
    "src.windows.onboarding", "src.windows.settings",
]
hiddenimports += collect_submodules("src.windows")

datas = [
    ("config.json", "."),
    ("assets/freeflow.ico", "assets"),
]
for root, _, files in os.walk("src/windows"):
    for f in files:
        if f.lower().endswith((".html", ".css", ".js", ".png", ".svg")):
            src = os.path.join(root, f)
            datas.append((src, os.path.dirname(src).replace("\\", "/")))
# Self-hosted fonts (Space Grotesk + JetBrains Mono) — required for offline
# rendering. fonts.py reads these from sys._MEIPASS/src/assets/fonts/ at import.
for root, _, files in os.walk("src/assets"):
    for f in files:
        if f.lower().endswith((".woff2", ".woff", ".ttf", ".otf")):
            src = os.path.join(root, f)
            datas.append((src, os.path.dirname(src).replace("\\", "/")))

binaries = []
for pkg in ("faster_whisper", "ctranslate2", "sounddevice",
            "onnxruntime", "pystray", "webview"):
    try:
        d, b, h = collect_all(pkg)
        datas += d; binaries += b; hiddenimports += h
    except Exception:
        pass

a = Analysis(
    ["src/main.py"],
    pathex=[os.path.abspath(".")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest", "IPython", "jupyter", "notebook",
        # `av` (PyAV) CANNOT be excluded: faster_whisper/__init__.py imports
        # `decode_audio` from faster_whisper/audio.py which does `import av`
        # at module-load time. Excluding breaks even before we pass any audio.
        "pip", "setuptools", "PyInstaller",  # never needed at runtime
        "pywin.debugger", "win32com.test",   # COM dev tools
        "pygments",            # syntax highlighting (only used by `rich`)
        "hf_xet",              # HF transfer accelerator (only useful for >10 GB models)
        "tkinter.test", "test", "unittest",
        "lib2to3", "xml.dom.minidom", "xmlrpc", "pydoc_data",
        "asyncio.test_utils", "doctest",
        "tornado", "zmq",      # not used
        # Cannot exclude `distutils` (PyInstaller pre-hook aliases it).
        # Cannot exclude `argparse` (used transitively).
        # Cannot exclude `pythonwin` (breaks `pywintypes` chain on some builds).
    ],
    noarchive=False,
    optimize=0,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON,
    version=None,
)
