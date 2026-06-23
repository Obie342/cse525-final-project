"""Audio processing and LED visualization functions."""

from __future__ import annotations

import time
import wave
from pathlib import Path
from threading import Event

import numpy as np

from .hardware import Strip, rgb


def color_wheel(position: int) -> int:
    position %= 256
    if position < 85:
        return rgb(position * 3, 255 - position * 3, 0)
    if position < 170:
        position -= 85
        return rgb(255 - position * 3, 0, position * 3)
    position -= 170
    return rgb(0, position * 3, 255 - position * 3)


def clear_strip(strip: Strip) -> None:
    for index in range(strip.numPixels()):
        strip.setPixelColor(index, rgb(0, 0, 0))
    strip.show()


def process_audio_chunk(data: bytes, strip: Strip, settings: dict) -> None:
    samples = np.frombuffer(data, dtype=np.int16)
    if samples.size == 0:
        return

    # A bar-style volume meter is clearer on a linear strip than one FFT bin per LED.
    normalized_level = min(1.0, float(np.sqrt(np.mean(samples.astype(np.float64) ** 2))) / 12_000.0)
    lit_count = int(round(normalized_level * strip.numPixels()))

    pattern = settings.get("pattern", "rainbow")
    selected = settings.get("color", {"r": 255, "g": 255, "b": 255})

    for index in range(strip.numPixels()):
        if index >= lit_count:
            color = rgb(0, 0, 0)
        elif pattern == "single_color":
            color = rgb(selected["r"], selected["g"], selected["b"])
        else:
            color = color_wheel(index * 256 // max(1, strip.numPixels()))
        strip.setPixelColor(index, color)
    strip.show()


def visualize_wave_file(
    file_path: str | Path,
    strip: Strip,
    settings: dict,
    stop_event: Event,
    chunk_size: int,
) -> None:
    with wave.open(str(file_path), "rb") as wave_file:
        if wave_file.getsampwidth() != 2:
            raise ValueError("Only 16-bit PCM WAV files are currently supported.")

        frame_rate = wave_file.getframerate()
        channels = wave_file.getnchannels()

        while not stop_event.is_set():
            data = wave_file.readframes(chunk_size)
            if not data:
                break

            if channels > 1:
                samples = np.frombuffer(data, dtype=np.int16).reshape(-1, channels)
                data = samples.mean(axis=1).astype(np.int16).tobytes()

            process_audio_chunk(data, strip, settings)
            time.sleep(chunk_size / frame_rate)


def visualize_live_audio(
    strip: Strip,
    settings: dict,
    stop_event: Event,
    rate: int,
    chunk_size: int,
    input_device_index: int | None,
) -> None:
    try:
        import pyaudio
    except ImportError as exc:
        raise RuntimeError("PyAudio is required for live microphone mode.") from exc

    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=rate,
        input=True,
        input_device_index=input_device_index,
        frames_per_buffer=chunk_size,
    )
    try:
        while not stop_event.is_set():
            data = stream.read(chunk_size, exception_on_overflow=False)
            process_audio_chunk(data, strip, settings)
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
