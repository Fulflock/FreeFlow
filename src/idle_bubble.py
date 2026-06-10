"""Floating FF speech-bubble idle indicator.

A small frameless tkinter Toplevel rendered with a magenta transparent-color
key so the canvas appears truly floating on the desktop (no rectangle).

The bubble is drawn with Canvas primitives:
  - drop shadow (offset pink polygon at low intensity)
  - pink speech-bubble polygon with dark stroke
  - dark "ff" lettering (drawn as small polygons for crispness)
  - tiny sparkle dots (top right)

Runs in a daemon thread so it can coexist with pywebview's blocking main loop.
"""

import ctypes
import threading
import tkinter as tk

# Make this Python process per-monitor DPI-aware BEFORE any tk window exists,
# so tkinter and Win32 agree on coordinates and the bubble lands where we ask.
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


# ── Colors ──────────────────────────────────────────────────────────────────
PINK = "#ff5d8f"
PINK_SHADOW = "#ffb4c8"   # softer pink for drop shadow
INK = "#16140f"
CREAM = "#fffdf7"         # FF letter color — matches assets/freeflow.ico
TRANSPARENT = "magenta"   # color-key used by Win32 to punch-through


# ── Bubble geometry (matches the SVG viewBox 64x56 scaled to render size) ──
# The bubble must be the SAME PHYSICAL size on every screen. The process is
# per-monitor DPI-aware (set above), so tkinter works in PHYSICAL pixels —
# a fixed size therefore looks tiny on a 200% screen and HUGE on a 100% one.
# So scale by the real monitor DPI: 96 dpi (100%) → 1.0, 192 dpi (200%) → 2.0.
# (A hardcoded SCALE=2, calibrated on a 200% laptop, made the bubble twice too
#  big on a friend's 100% display — this is the fix.)
def _dpi_scale():
    try:
        return max(1.0, ctypes.windll.user32.GetDpiForSystem() / 96.0)
    except Exception:
        return 1.0

SCALE = _dpi_scale()
BUBBLE_W = round(40 * SCALE)
BUBBLE_H = round(36 * SCALE)
PAD = round(6 * SCALE)      # canvas padding to give room for the drop shadow + float
CANVAS_W = BUBBLE_W + PAD * 2
CANVAS_H = BUBBLE_H + PAD * 2 + round(4 * SCALE)


_SX = BUBBLE_W / 64.0
_SY = BUBBLE_H / 56.0


def _bubble_points(ox=0, oy=0, scale_x=None, scale_y=None):
    if scale_x is None:
        scale_x = _SX
    if scale_y is None:
        scale_y = _SY
    """Return canvas-coordinate points for the speech bubble outline.

    Approximates the rounded-rect-with-tail using straight segments —
    Tk's create_polygon with smooth=True yields a curved look identical
    to the SVG counterpart at this size.
    """
    # SVG path:
    #   M10 6  H54  arc to (60,12)  V36  arc to (54,42)
    #   H30  L20 52 L22 42  H10  arc to (4,36)  V12  arc to (10,6)
    raw = [
        (10, 6), (54, 6),
        (57, 7), (60, 12),
        (60, 36),
        (57, 41), (54, 42),
        (30, 42),
        (20, 52),
        (22, 42),
        (10, 42),
        (7, 41), (4, 36),
        (4, 12),
        (7, 7), (10, 6),
    ]
    return [
        (ox + x * scale_x, oy + y * scale_y) for (x, y) in raw
    ]


def _f_letter_points(left_x, scale_x=None, scale_y=None, oy=0):
    if scale_x is None:
        scale_x = _SX
    if scale_y is None:
        scale_y = _SY
    """Single 'F' as a polygon, matching the SVG path:
       M19 33 V16 H29 V20 H23 V23.5 H28 V27.5 H23 V33 Z
       Shifted by `left_x` (in SVG units) for the second F.
    """
    raw = [
        (19, 33),
        (19, 16),
        (29, 16),
        (29, 20),
        (23, 20),
        (23, 23.5),
        (28, 23.5),
        (28, 27.5),
        (23, 27.5),
        (23, 33),
    ]
    return [
        ((p[0] + left_x) * scale_x, (p[1] * scale_y) + oy)
        for p in raw
    ]


# ── Idle bubble window ─────────────────────────────────────────────────────
class IdleBubble:
    """Floating FF bubble — runs tkinter in its own daemon thread."""

    def __init__(self, gap_above_taskbar=80):
        self._gap = gap_above_taskbar
        self._root = None
        self._canvas = None
        self._float_offset = 0
        self._float_dir = 1
        self._visible = False
        self._ready = threading.Event()
        self._thread = None

    # ---- lifecycle --------------------------------------------------------
    def start(self):
        """Spin up the tkinter mainloop in a daemon thread."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        # Wait briefly so callers can call .show()/.hide() without races
        self._ready.wait(timeout=2.0)

    def _run(self):
        try:
            self._root = tk.Tk()
            self._root.withdraw()
            self._root.overrideredirect(True)
            self._root.attributes("-topmost", True)
            try:
                self._root.attributes("-transparentcolor", TRANSPARENT)
            except tk.TclError:
                # -transparentcolor is Windows-only; degrade gracefully
                pass
            self._root.configure(bg=TRANSPARENT)

            # Skip taskbar/alt-tab. We deliberately do NOT add WS_EX_LAYERED
            # or WS_EX_TRANSPARENT — tkinter's -transparentcolor already sets
            # up its own layered-window plumbing, and forcing those flags here
            # leaves the window invisible (layered without proper alpha).
            try:
                self._root.update_idletasks()
                hwnd = ctypes.windll.user32.GetParent(self._root.winfo_id())
                GWL_EXSTYLE = -20
                # WS_EX_TOOLWINDOW (0x80) | WS_EX_NOACTIVATE (0x08000000)
                ex = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                ex |= 0x80 | 0x08000000
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex)
            except Exception:
                pass

            self._canvas = tk.Canvas(
                self._root,
                width=CANVAS_W,
                height=CANVAS_H,
                bg=TRANSPARENT,
                highlightthickness=0,
                bd=0,
            )
            self._canvas.pack()

            self._draw_bubble()
            self._place_bottom_center()

            self._ready.set()
            self._animate_float()
            self._root.mainloop()
        except Exception:
            import traceback
            traceback.print_exc()
            self._ready.set()  # unblock callers even on failure

    # ---- drawing ----------------------------------------------------------
    def _draw_bubble(self):
        c = self._canvas
        # Drop shadow — same polygon, offset 2px down, in soft pink
        shadow_pts = _bubble_points(ox=PAD + SCALE, oy=PAD + 3 * SCALE)
        c.create_polygon(
            *[coord for pt in shadow_pts for coord in pt],
            fill=PINK_SHADOW,
            outline="",
            smooth=True,
            splinesteps=24,
            tags=("bubble",),
        )

        # Main bubble (pink fill + dark stroke)
        bubble_pts = _bubble_points(ox=PAD, oy=PAD)
        c.create_polygon(
            *[coord for pt in bubble_pts for coord in pt],
            fill=PINK,
            outline=INK,
            width=2.5 * SCALE,
            smooth=True,
            splinesteps=24,
            tags=("bubble",),
        )

        # "f f" letters in CREAM — matches the .ico exactly (pink bubble + cream FF)
        f1 = _f_letter_points(0, oy=PAD)
        f2 = _f_letter_points(14, oy=PAD)  # second F shifted +14 in SVG units
        for pts in (f1, f2):
            offset_pts = [(x + PAD, y) for (x, y) in pts]
            c.create_polygon(
                *[coord for pt in offset_pts for coord in pt],
                fill=INK,
                outline=INK,
                width=1,
                tags=("bubble",),
            )

        # Tiny sparkle dots (top-right of the bubble) — cream too
        sx = PAD + 49 * _SX
        sy = PAD + 12 * _SY
        r = 1.4 * SCALE
        c.create_oval(sx - r, sy - r, sx + r, sy + r,
                      fill=INK, outline="", tags=("bubble",))
        sx2 = PAD + 53 * _SX
        sy2 = PAD + 12 * _SY
        r2 = 1.0 * SCALE
        c.create_oval(sx2 - r2, sy2 - r2, sx2 + r2, sy2 + r2,
                      fill=INK, outline="", tags=("bubble",))

    # ---- placement --------------------------------------------------------
    def _place_bottom_center(self):
        """Position the window at bottom-center.

        With the process being per-monitor DPI-aware (set at module import),
        GetSystemMetrics returns physical pixels and tkinter's `geometry()`
        uses physical pixels too, so the math is straightforward.
        """
        try:
            user32 = ctypes.windll.user32
            sw = user32.GetSystemMetrics(0)
            sh = user32.GetSystemMetrics(1)
        except Exception:
            sw = self._root.winfo_screenwidth()
            sh = self._root.winfo_screenheight()
        x = (sw - CANVAS_W) // 2
        y = sh - CANVAS_H - self._gap
        self._root.geometry(f"{CANVAS_W}x{CANVAS_H}+{x}+{y}")
        self._root.update_idletasks()

    # ---- subtle float animation ------------------------------------------
    def _animate_float(self):
        if not self._canvas or not self._root:
            return
        try:
            # Move every shape with the "bubble" tag by 1px on the vertical axis
            self._canvas.move("bubble", 0, self._float_dir)
            self._float_offset += self._float_dir
            if self._float_offset >= 3 or self._float_offset <= -3:
                self._float_dir = -self._float_dir
            self._root.after(80, self._animate_float)
        except Exception:
            pass

    # ---- public api -------------------------------------------------------
    def show(self):
        if not self._root:
            return
        self._visible = True
        try:
            self._root.after(0, self._root.deiconify)
            self._root.after(0, lambda: self._root.attributes("-topmost", True))
        except Exception:
            pass

    def hide(self):
        if not self._root:
            return
        self._visible = False
        try:
            self._root.after(0, self._root.withdraw)
        except Exception:
            pass

    def stop(self):
        if not self._root:
            return
        try:
            self._root.after(0, self._root.destroy)
        except Exception:
            pass
