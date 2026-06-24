# Archive

Historical artifacts from CSE 525 development. Not used by the current application.

## `main_test3_fft_monolith.py`

Original single-file Flask prototype (December 2024 era). Superseded by the modular `audio_led_visualizer/` package in the June 2026 repository refresh.

- **FFT-based** spectrum visualization (frequency bins mapped to LEDs)
- Monolithic layout: Flask routes, threading, PyAudio, and `rpi_ws281x` in one file
- Requires Raspberry Pi hardware; no mock strip for off-device development
- Saves uploads to `./uploaded_files/` and uses route names incompatible with current templates

Kept for reference only. Run `app.py` and the `audio_led_visualizer/` package instead.
