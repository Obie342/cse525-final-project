from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import threading
import numpy as np
import pyaudio
from rpi_ws281x import PixelStrip, Color
import wave
import time

# Flask setup
app = Flask(__name__)

# LED strip configuration
LED_COUNT = 144
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 255
LED_INVERT = False
LED_CHANNEL = 0

# Initialize LED strip
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# Visualization control
visualization_thread = None
stop_visualization = threading.Event()

# Settings dictionary
settings = {
    "brightness": 255,
    "pattern": "rainbow",
    "color": {"r": 255, "g": 255, "b": 255}
}

def process_audio_chunk_fft(data, strip):
    """Visualize audio spectrum on the LEDs using FFT."""
    audio_data = np.frombuffer(data, dtype=np.int16)
    fft_result = np.abs(np.fft.rfft(audio_data))
    fft_normalized = np.interp(fft_result, (fft_result.min(), fft_result.max()), (0, LED_COUNT))

    # Set a threshold to filter out noise
    noise_threshold = 150000  # Adjust this value as needed
    fft_normalized = np.where(fft_result > noise_threshold, fft_normalized, 0)

    # Light up LEDs based on FFT result
    for i in range(LED_COUNT):
        if i < len(fft_normalized) and fft_normalized[i] > i:
            strip.setPixelColor(i, Color(settings["color"]["r"],settings["color"]["g"],settings["color"]["b"]))
        else:
            strip.setPixelColor(i, Color(0, 0, 0))  # Off for inactive LEDs
    strip.show()

def visualize_live_audio():
    """Capture live audio and visualize it using FFT."""
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=512)  # Reduce buffer size for faster refresh
    try:
        while not stop_visualization.is_set():
            data = stream.read(512, exception_on_overflow=False)  # Smaller buffer for quicker updates
            process_audio_chunk_fft(data, strip)
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
def visualize_audio_file(file_path):
    """Visualize a .wav file using FFT."""
    try:
        with wave.open(file_path, "rb") as wf:
            sample_rate = wf.getframerate()
            chunk_size = 512

            while not stop_visualization.is_set():
                data = wf.readframes(chunk_size)
                if not data:
                    break
                process_audio_chunk_fft(data, strip)
                time.sleep(chunk_size / sample_rate)
    except Exception as e:
        print(f"Error visualizing file: {e}")

'''def visualize_audio_file(file_path):
    """Visualize a .wav file using FFT and play it."""
    try:
        with wave.open(file_path, "rb") as wf:
            p = pyaudio.PyAudio()
            stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )

            chunk_size = 512
            while not stop_visualization.is_set():
                data = wf.readframes(chunk_size)
                if not data:
                    break
                # Write audio to PyAudio's stream
                stream.write(data)
                # Visualize the same audio chunk
                process_audio_chunk_fft(data, strip)

            stream.stop_stream()
            stream.close()
            p.terminate()
    except Exception as e:
        print(f"Error visualizing and playing file: {e}")
'''
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/live', methods=['GET', 'POST'])
def live():
    if request.method == 'GET':
        return redirect(url_for('index'))  # Redirect to homepage for GET
    # POST: Start live audio visualization
    global visualization_thread
    stop_visualization.clear()
    visualization_thread = threading.Thread(target=visualize_live_audio)
    visualization_thread.start()
    return redirect(url_for('index'))

@app.route('/file', methods=['GET', 'POST'])
def file():
    if request.method == 'GET':
        # Render the file upload page
        return render_template('file.html')

    if 'file' not in request.files:
        # Handle cases where no file is uploaded
        return redirect(url_for('index'))

    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        # Handle cases where no file is selected
        return redirect(url_for('index'))

    if uploaded_file and uploaded_file.filename.endswith('.wav'):
        # Save the uploaded .wav file
        file_path = os.path.join('./uploaded_files', uploaded_file.filename)
        uploaded_file.save(file_path)

        # Start audio visualization for the uploaded file
        global visualization_thread
        stop_visualization.clear()
        visualization_thread = threading.Thread(target=visualize_audio_file, args=(file_path,))
        visualization_thread.start()

        return render_template('file.html', filename=uploaded_file.filename)

@app.route('/uploaded_audio/<filename>')
def uploaded_audio(filename):
    """Serve the uploaded audio file."""
    return send_from_directory('./uploaded_files', filename)

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    global settings
    if request.method == 'POST':
        # Update brightness
        settings["brightness"] = int(request.form.get("brightness", settings["brightness"]))
        strip.setBrightness(settings["brightness"])

        # Update pattern
        settings["pattern"] = request.form.get("pattern", settings["pattern"])

        # Update single color
        settings["color"]["r"] = int(request.form.get("red", settings["color"]["r"]))
        settings["color"]["g"] = int(request.form.get("green", settings["color"]["g"]))
        settings["color"]["b"] = int(request.form.get("blue", settings["color"]["b"]))

        return redirect(url_for('settings_page'))

    return render_template('settings.html', settings=settings)

@app.route('/stop', methods=['GET', 'POST'])
def stop():
    if request.method == 'GET':
        return redirect(url_for('index'))  # Redirect to homepage for GET
    # POST: Stop visualization
    stop_visualization.set()
    if visualization_thread:
        visualization_thread.join()
    return redirect(url_for('index'))

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        # Turn off LEDs on exit
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()

