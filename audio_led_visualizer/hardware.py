"""LED strip abstraction with a safe development fallback."""

from __future__ import annotations

import logging
from typing import Protocol

logger = logging.getLogger(__name__)

try:
    from rpi_ws281x import Color as _Color
    from rpi_ws281x import PixelStrip
except (ImportError, RuntimeError):
    _Color = None
    PixelStrip = None


def rgb(r: int, g: int, b: int) -> int:
    """Return a color value understood by either the real or mock strip."""
    r, g, b = (max(0, min(255, int(value))) for value in (r, g, b))
    if _Color is not None:
        return _Color(r, g, b)
    return (r << 16) | (g << 8) | b


class Strip(Protocol):
    def begin(self) -> None: ...
    def numPixels(self) -> int: ...
    def setPixelColor(self, index: int, color: int) -> None: ...
    def setBrightness(self, brightness: int) -> None: ...
    def show(self) -> None: ...


class MockPixelStrip:
    """In-memory strip used when Raspberry Pi libraries are unavailable."""

    def __init__(self, count: int, brightness: int = 255) -> None:
        self._pixels = [0] * count
        self._brightness = brightness

    def begin(self) -> None:
        logger.warning("Using mock LED strip; no physical LEDs will be controlled.")

    def numPixels(self) -> int:
        return len(self._pixels)

    def setPixelColor(self, index: int, color: int) -> None:
        if 0 <= index < len(self._pixels):
            self._pixels[index] = color

    def setBrightness(self, brightness: int) -> None:
        self._brightness = max(0, min(255, int(brightness)))

    def show(self) -> None:
        return


def create_strip(config: dict) -> Strip:
    count = int(config["LED_COUNT"])
    brightness = int(config["LED_BRIGHTNESS"])

    if PixelStrip is None:
        strip: Strip = MockPixelStrip(count, brightness)
    else:
        try:
            strip = PixelStrip(
                count,
                int(config["LED_PIN"]),
                int(config["LED_FREQ_HZ"]),
                int(config["LED_DMA"]),
                bool(config["LED_INVERT"]),
                brightness,
                int(config["LED_CHANNEL"]),
            )
        except Exception:
            logger.exception("Could not initialize the physical LED strip; using mock mode.")
            strip = MockPixelStrip(count, brightness)

    strip.begin()
    return strip
