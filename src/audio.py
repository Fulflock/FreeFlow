import threading
from typing import Optional

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "float32"
BLOCKSIZE = 1024


class AudioRecorder:
    def __init__(self, device: Optional[int] = None):
        self._device = device
        self._chunks: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._stream: Optional[sd.InputStream] = None
        self._last_error: Optional[str] = None

    def _callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        if status:
            # Don't crash — just record the warning for later inspection.
            self._last_error = f"audio callback warning: {status}"
        with self._lock:
            self._chunks.append(indata.copy())

    def start_recording(self) -> None:
        with self._lock:
            self._chunks.clear()
        try:
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=BLOCKSIZE,
                device=self._device,
                callback=self._callback,
            )
            self._stream.start()
            # Successful start — clear any stale error from a previous attempt.
            self._last_error = None
        except Exception as e:
            self._stream = None
            self._last_error = str(e)
            raise RuntimeError(f"Microphone unavailable: {e}") from e

    def get_last_error(self) -> Optional[str]:
        return self._last_error

    def get_current_amplitude(self) -> float:
        """Return current audio RMS amplitude (0.0 - 1.0) from recent chunks.

        Used by the UI waveform to make bars react to actual voice level.
        """
        with self._lock:
            if not self._chunks:
                return 0.0
            # Take the last few chunks (~last 100ms) for responsiveness.
            recent = self._chunks[-3:] if len(self._chunks) >= 3 else self._chunks
        try:
            arr = np.concatenate(recent).flatten()
            rms = float(np.sqrt(np.mean(arr ** 2)))
            # Aggressive boost so even quiet/medium voices visibly drive the
            # waveform. RMS for normal speech ≈ 0.01–0.04 → amp 0.25–1.0.
            amp = min(1.0, rms * 25.0)
            # Floor: always show a tiny baseline so the bars never freeze flat.
            return max(amp, 0.08)
        except Exception:
            return 0.0

    def stop_recording(self) -> np.ndarray:
        # Detach the stream from the recorder immediately so the hotkey-release
        # thread isn't blocked by stop()/close() (which can take 50-200ms on
        # WASAPI). The close runs in a daemon thread.
        stream = self._stream
        self._stream = None
        if stream is not None:
            def _close_async(s):
                try:
                    s.stop()
                    s.close()
                except Exception:
                    import traceback
                    traceback.print_exc()
            threading.Thread(target=_close_async, args=(stream,), daemon=True).start()
        with self._lock:
            if not self._chunks:
                return np.empty(0, dtype=np.float32)
            audio = np.concatenate(self._chunks).flatten()
            self._chunks.clear()
        return audio

    @classmethod
    def get_input_devices(cls) -> list[dict]:
        devices = sd.query_devices()
        return [
            {"index": i, "name": d["name"], "channels": d["max_input_channels"]}
            for i, d in enumerate(devices)
            if d["max_input_channels"] > 0
        ]
