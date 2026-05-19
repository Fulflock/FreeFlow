# FreeFlow

**Free, open-source voice dictation that runs 100% locally on your machine.**

No subscription. No cloud. No data sent anywhere. Just speak and paste.

https://github.com/user-attachments/assets/demo-placeholder

## Why FreeFlow?

| | Paid alternatives | FreeFlow |
|---|---|---|
| Price | $15/month | **Free forever** |
| Privacy | Voice sent to cloud | **100% local** |
| Works offline | No | **Yes** |
| Open source | No | **Yes** |

## How it works

1. Press and hold `Ctrl+Space`
2. Speak
3. Release — your speech is transcribed instantly
4. Click where you want the text — it's pasted automatically

Works in **any application** — browser, Word, Slack, VS Code, Discord, anything.

## Install (2 minutes)

### Option 1: Download the .exe (easiest)

1. Download `FreeFlow.exe` from [Releases](../../releases)
2. Run it
3. Done

### Option 2: From source

```bash
# Requires Python 3.12+
git clone https://github.com/Fulflock/FreeFlow.git
cd FreeFlow
pip install -r requirements.txt
python -m src.main
```

## Features

- **Push-to-talk** — Hold `Ctrl+Space`, speak, release
- **Click-to-paste** — Text waits for you to click where you want it
- **Smart cleanup** — Removes filler words ("um", "uh", "euh")
- **Punctuation** — Automatic capitalization and punctuation
- **Dictation history** — All your dictations saved locally in `~/.freeflow/history/`
- **System tray** — Runs quietly in the background
- **Floating overlay** — Shows recording/transcription status
- **French & English** — Change language in `config.json`
- **Fully offline** — Uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper) locally

## Configuration

Edit `config.json`:

```json
{
  "hotkey_combo": ["ctrl", "space"],
  "language": "fr",
  "model_size": "small",
  "overlay_opacity": 0.85
}
```

**Models:** `base` (fast, ~150MB) | `small` (balanced, ~500MB) | `medium` (accurate, ~1.5GB) | `large-v3` (best, ~3GB)

## Requirements

- Windows 10/11
- Python 3.12+ (if running from source)
- ~500MB RAM (with `small` model)
- No GPU needed — runs on CPU

## Tech stack

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — CTranslate2-optimized Whisper
- [sounddevice](https://python-sounddevice.readthedocs.io/) — Audio capture
- [pynput](https://github.com/moses-palmer/pynput) — Global hotkeys
- [pystray](https://github.com/moses-palmer/pystray) — System tray
- tkinter — Floating overlay

## License

MIT — do whatever you want with it.

---

If this is useful to you, consider giving it a star.
