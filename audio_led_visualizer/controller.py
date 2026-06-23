"""Thread-safe visualization lifecycle management."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Callable

from .hardware import Strip
from .visualizer import clear_strip, visualize_live_audio, visualize_wave_file

logger = logging.getLogger(__name__)


class VisualizationController:
    def __init__(self, strip: Strip, config: dict) -> None:
        self.strip = strip
        self.config = config
        self.settings = {
            "brightness": int(config["LED_BRIGHTNESS"]),
            "pattern": "rainbow",
            "color": {"r": 255, "g": 255, "b": 255},
        }
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.last_error: str | None = None
        self._lock = threading.Lock()

    @property
    def running(self) -> bool:
        return self.thread is not None and self.thread.is_alive()

    def _run(self, target: Callable, *args) -> None:
        try:
            target(*args)
        except Exception as exc:
            logger.exception("Visualization failed")
            self.last_error = str(exc)
        finally:
            clear_strip(self.strip)

    def _start(self, target: Callable, *args) -> None:
        with self._lock:
            self.stop(wait=True)
            self.last_error = None
            self.stop_event.clear()
            self.thread = threading.Thread(
                target=self._run,
                args=(target, *args),
                daemon=True,
                name="audio-led-visualizer",
            )
            self.thread.start()

    def start_live(self) -> None:
        self._start(
            visualize_live_audio,
            self.strip,
            self.settings,
            self.stop_event,
            int(self.config["AUDIO_RATE"]),
            int(self.config["AUDIO_CHUNK_SIZE"]),
            self.config.get("AUDIO_INPUT_DEVICE_INDEX"),
        )

    def start_file(self, file_path: str | Path) -> None:
        self._start(
            visualize_wave_file,
            file_path,
            self.strip,
            self.settings,
            self.stop_event,
            int(self.config["AUDIO_CHUNK_SIZE"]),
        )

    def update_settings(self, brightness: int, pattern: str, r: int, g: int, b: int) -> None:
        self.settings["brightness"] = max(0, min(255, brightness))
        self.settings["pattern"] = pattern if pattern in {"rainbow", "single_color"} else "rainbow"
        self.settings["color"] = {
            "r": max(0, min(255, r)),
            "g": max(0, min(255, g)),
            "b": max(0, min(255, b)),
        }
        self.strip.setBrightness(self.settings["brightness"])

    def stop(self, wait: bool = True) -> None:
        thread = self.thread
        self.stop_event.set()
        if wait and thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=2.0)
        if thread is not None and not thread.is_alive():
            self.thread = None
        clear_strip(self.strip)

    def shutdown(self) -> None:
        self.stop(wait=True)
