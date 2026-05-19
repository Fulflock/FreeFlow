import threading
import tkinter as tk
from PIL import Image, ImageDraw
import pystray


class Overlay:
    WIDTH, HEIGHT = 420, 60
    BG = "#1a1a2e"

    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.85)
        self.root.configure(bg=self.BG)

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = screen_w - self.WIDTH - 20
        y = screen_h - self.HEIGHT - 60
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        self.canvas = tk.Canvas(
            self.root, width=self.WIDTH, height=self.HEIGHT,
            bg=self.BG, highlightthickness=0,
        )
        self.canvas.pack()
        self._dot = self.canvas.create_oval(16, 20, 30, 34, fill="#00d4aa", outline="")
        self._text = self.canvas.create_text(
            45, self.HEIGHT // 2, anchor="w",
            text="", fill="white", font=("Segoe UI", 11),
        )

    def show(self, text: str, color: str = "#00d4aa"):
        self.canvas.itemconfig(self._dot, fill=color)
        self.canvas.itemconfig(self._text, text=text)
        self.root.deiconify()

    def hide(self):
        self.root.withdraw()

    def update_text(self, text: str):
        self.canvas.itemconfig(self._text, text=text)

    def schedule(self, callback):
        self.root.after(0, callback)

    def mainloop(self):
        self.root.mainloop()

    def destroy(self):
        self.root.quit()


class TrayIcon:
    COLORS = {"ready": "#00d4aa", "recording": "#ff8c00", "transcribing": "#4ea8de"}

    def __init__(self, on_quit):
        self._on_quit = on_quit
        self._icon: pystray.Icon | None = None
        self._thread: threading.Thread | None = None

    @staticmethod
    def _make_icon(color: str) -> Image.Image:
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([12, 12, 52, 52], fill=color)
        return img

    def start(self):
        menu = pystray.Menu(
            pystray.MenuItem("WhisperFlow", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quitter", lambda: self._on_quit()),
        )
        self._icon = pystray.Icon(
            "whisperflow", self._make_icon(self.COLORS["ready"]),
            "WhisperFlow", menu,
        )
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def set_state(self, state: str):
        if self._icon:
            self._icon.icon = self._make_icon(self.COLORS.get(state, self.COLORS["ready"]))

    def stop(self):
        if self._icon:
            self._icon.stop()


class WhisperFlowUI:
    def __init__(self, opacity: float = 0.85, on_quit=None):
        self._external_quit = on_quit
        self.overlay = Overlay()
        self.overlay.root.attributes("-alpha", opacity)
        self.tray = TrayIcon(on_quit=self.quit)

    def start(self):
        self.tray.start()
        self.overlay.mainloop()

    def show_recording(self):
        def _update():
            self.overlay.show("Enregistrement...", "#ff8c00")
            self.tray.set_state("recording")
        self.overlay.schedule(_update)

    def show_transcribing(self):
        def _update():
            self.overlay.show("Transcription...", "#4ea8de")
            self.tray.set_state("transcribing")
        self.overlay.schedule(_update)

    def show_result(self, text: str):
        def _update():
            display = text if len(text) <= 55 else text[:52] + "..."
            self.overlay.show(display, "#00d4aa")
            self.tray.set_state("ready")
            self.overlay.root.after(5000, lambda: self.overlay.hide())
        self.overlay.schedule(_update)

    def show_click_to_paste(self, text: str):
        from src.injector import _lock, _pending_text
        def _update():
            display = text if len(text) <= 45 else text[:42] + "..."
            self.overlay.show(">> " + display, "#f0c040")
            self.tray.set_state("ready")
            self._poll_paste_done()
        self.overlay.schedule(_update)

    def _poll_paste_done(self):
        from src.injector import _lock, _pending_text
        with _lock:
            still_pending = _pending_text is not None
        if still_pending:
            self.overlay.root.after(100, self._poll_paste_done)
        else:
            self.overlay.show("Collé !", "#00d4aa")
            self.overlay.root.after(1500, lambda: self.overlay.hide())

    def hide(self):
        def _update():
            self.overlay.hide()
            self.tray.set_state("ready")
        self.overlay.schedule(_update)

    def stop(self):
        self.quit()

    def quit(self):
        self.tray.stop()
        self.overlay.schedule(self.overlay.destroy)
        if self._external_quit:
            self._external_quit()
