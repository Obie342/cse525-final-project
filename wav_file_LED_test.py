import numpy as np
import wave
import time
from rpi_ws281x import PixelStrip, Color

# LED strip configuration:
LED_COUNT = 144          # Number of LEDs
LED_PIN = 18            # GPIO pin connected to the LEDs (PWM0)
LED_FREQ_HZ = 800000    # LED signal frequency 800 kbps (datasheet)
LED_DMA = 10            # DMA channel to use for generating signal
LED_BRIGHTNESS = 255    # Brightness (0-255)
LED_INVERT = False      # True to invert signal
LED_CHANNEL = 0         # Channel (0 or 1)

# Initialize LED strip
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

def color_wheel(pos):
    """Generate rainbow colors across 0-255 positions"""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def visualize_audio(file_path):
    """Play audio and visualize on LEDs."""
    with wave.open(file_path, "rb") as wf:
        # extract audio parameters
        sample_rate = wf.getframerate()
        chunk_size = 1024  # Number of frames per chunk

        # prepare LEDs
        strip.show()

        # Process audio chunks
        while (data := wf.readframes(chunk_size)):
            # Convert audio data to numpy array
            audio_data = np.frombuffer(data, dtype=np.int16)
            
            # Apply FFT to get frequency data # fast fourier transform
            fft = np.abs(np.fft.rfft(audio_data))
            fft = fft[:LED_COUNT]  # Limit to number of LEDs

            # Normalize frequency data to 0-255 range
            fft_normalized = np.interp(fft, (fft.min(), fft.max()), (0, 255))
            
            # Map frequency data to LED colors
            for i in range(LED_COUNT):
                brightness = int(fft_normalized[i])
                color = color_wheel(i * 256 // LED_COUNT)  # Create a rainbow effect
                strip.setPixelColor(i, Color(brightness, brightness, brightness))

            strip.show()
            time.sleep(chunk_size / sample_rate)  # Sync with audio playback

try:
    visualize_audio("CantinaBand60.wav")  # CantinaBand60.wav
finally:
    # Clean up LEDs on exit
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()
