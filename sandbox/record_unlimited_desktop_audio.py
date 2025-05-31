# record_desktop_audio.py
import soundcard as sc
import soundfile as sf
import numpy as np
import warnings
import msvcrt  # For Windows key press detection
import threading
import tkinter as tk

# Suppress the SoundcardRuntimeWarning
warnings.filterwarnings("ignore", category=sc.SoundcardRuntimeWarning)

OUTPUT_FILE_NAME = "out_test.wav"
SAMPLE_RATE = 48000
CHUNK_SEC = 1  # Record in 1-second chunks

frames = []
is_recording = False  # Global flag

def start_recording():
    global is_recording
    if is_recording:
        print("Already recording. Please stop the current recording before starting a new one.")
        return
    print("Starting recording...")
    is_recording = True
    threading.Thread(target=record_audio).start()

def stop_recording():
    global is_recording
    if not is_recording:
        print("Not currently recording. Nothing to stop.")
        return
    print("Stopping recording...")
    is_recording = False

def record_audio():
    global is_recording
    frames.clear()
    print("Opening microphone/loopback device...")
    with sc.get_microphone(id=str(sc.default_speaker().name), include_loopback=True).recorder(samplerate=SAMPLE_RATE) as mic:
        print("Recording audio chunks...")
        while is_recording:
            data = mic.record(numframes=SAMPLE_RATE * CHUNK_SEC)
            frames.append(data)
    print("Finished recording. Concatenating audio data...")
    # Concatenate all recorded chunks
    audio = np.concatenate(frames, axis=0)

    # Save only the first channel; change to 'audio' for multi-channel
    print(f"Saving audio to {OUTPUT_FILE_NAME}...")
    sf.write(file=OUTPUT_FILE_NAME, data=audio[:, 0], samplerate=SAMPLE_RATE)
    print("Recording stopped and saved to", OUTPUT_FILE_NAME)

# Tkinter UI
root = tk.Tk()
tk.Button(root, text="Start Recording", command=start_recording).pack()
tk.Button(root, text="Stop Recording", command=stop_recording).pack()
root.mainloop()