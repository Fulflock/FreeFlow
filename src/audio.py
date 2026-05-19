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

    def _callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        with self._lock:
            self._chunks.append(indata.copy())

    def start_recording(self) -> None:
        with self._lock:
            self._chunks.clear()
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            blocksize=BLOCKSIZE,
            device=self._device,
            callback=self._callback,
        )
        self._stream.start()

    def stop_recording(self) -> np.ndarray:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
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
