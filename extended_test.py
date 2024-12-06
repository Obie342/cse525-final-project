import numpy as np
import pyaudio
import wave
import time
from rpi_ws281x import PixelStrip, Color
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# LED strip configuration
LED_COUNT = 144          # Number of LEDs
LED_PIN = 18            # GPIO pin connected to the LEDs (PWM0)
LED_FREQ_HZ = 800000    # LED signal frequency 800 kbps (datasheet)
LED_DMA = 10            # DMA channel to use
LED_BRIGHTNESS = 255    # Brightness (0-255)
LED_INVERT = False      # True to invert signal
LED_CHANNEL = 0         # Channel (0 or 1)

# Initialize LED strip
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

def color_wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def process_audio_chunk(data, strip):
    """Process a chunk of audio data and visualize it on the LEDs."""
    audio_data = np.frombuffer(data, dtype=np.int16)
    fft = np.abs(np.fft.rfft(audio_data))  # Fast Fourier Transform
    fft = fft[:LED_COUNT]  # Limit to number of LEDs
    fft_normalized = np.interp(fft, (fft.min(), fft.max()), (0, 255))

    for i in range(LED_COUNT):
        brightness = int(fft_normalized[i])
        color = color_wheel(i * 256 // LED_COUNT)
        strip.setPixelColor(i, Color(brightness, brightness, brightness))
    strip.show()

def visualize_live_audio():
    """Capture live audio from USB microphone and visualize it."""
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
    
    try:
        print("Visualizing live audio...")
        while True:
            data = stream.read(1024, exception_on_overflow=False)
            process_audio_chunk(data, strip)
    except KeyboardInterrupt:
        print("Stopping live audio visualization...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

def visualize_audio_file(file_path):
    """Play a .wav file and visualize it."""
    with wave.open(file_path, "rb") as wf:
        sample_rate = wf.getframerate()
        chunk_size = 1024

        print(f"Visualizing .wav file: {file_path}")
        while (data := wf.readframes(chunk_size)):
            process_audio_chunk(data, strip)
            time.sleep(chunk_size / sample_rate)

def select_wav_file():
    """Open a file dialog to select a .wav file."""
    Tk().withdraw()  # Hide main tkinter window
    file_path = askopenfilename(filetypes=[("WAV files", "*.wav")], title="Select a WAV file")
    if not file_path:
        print("No file selected. Exiting.")
        return None
    return file_path

def main():
    print("Select mode: 'live' (microphone) or 'file' (.wav playback)")
    mode = input("Mode: ").strip().lower()

    if mode == "live":
        visualize_live_audio()
    elif mode == "file":
        file_path = select_wav_file()
        if file_path:
            visualize_audio_file(file_path)
    else:
        print("Invalid mode selected. Exiting.")

if __name__ == "__main__":
    try:
        main()
    finally:
        # turn off all LEDs on exit
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
