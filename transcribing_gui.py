"""
LYRA: Transcibing Microphone Audio
"""

import pyaudio
import wave
import numpy as np
import os
import pyperclip
import time
import simpleaudio as sa
from faster_whisper import WhisperModel
import tkinter as tk
from tkinter import messagebox
from threading import Thread

recording = False
transcription_text = ""


def play_sound(file_path):
    try:
        wave_obj = sa.WaveObject.from_wave_file(file_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    except Exception as e:
        print(f"Error playing sound: {e}")


def record_audio(file_path="recorded_audio.wav", silence_timeout=20):
    global recording
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
    frames = []

    silence_threshold = 300
    silent_duration = 3
    silent_chunk_limit = silence_timeout * (16000 // 1024)

    try:
        while recording:
            data = stream.read(1024)
            frames.append(data)

            audio_data = np.frombuffer(data, dtype=np.int16)
            if np.abs(audio_data).mean() < silence_threshold:
                silent_duration += 1
            else:
                silent_duration = 0

            if silent_duration > silent_chunk_limit:
                break

    except Exception as e:
        print(f"Error during recording: {e}")

    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(file_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(frames))

    return file_path


def transcribe_audio(audio_file_path):
    print("Transcribing...")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_file_path)
    transcription = " ".join([segment.text for segment in segments])
    print("Transcription:", transcription)
    return transcription


def start_recording():
    global recording
    recording = True
    play_sound("audio/start_recording.wav")
    thread = Thread(target=record_process)
    thread.start()


def stop_recording():
    global recording
    recording = False
    play_sound("audio/stop_recording.wav")


def record_process():
    global transcription_text
    audio_path = "temp_recording.wav"
    record_audio(audio_path)
    transcription_text = transcribe_audio(audio_path)
    pyperclip.copy(transcription_text)
    os.remove(audio_path)
    show_transcription_popup(transcription_text)


def show_transcription_popup(text):
    popup = tk.Toplevel(root)
    popup.title("Transcription Result")
    text_field = tk.Text(popup, wrap="word", width=50, height=10)
    text_field.pack(padx=10, pady=10)
    text_field.insert("1.0", text)
    text_field.config(state="disabled")
    tk.Button(popup, text="Copy to Clipboard", command=copy_to_clipboard).pack(pady=5)
    tk.Button(popup, text="Close", command=popup.destroy).pack(pady=5)


def copy_to_clipboard():
    pyperclip.copy(transcription_text)
    messagebox.showinfo("Clipboard", "Transcription copied to clipboard!")


# GUI Setup
root = tk.Tk()
root.title("Lyra - Transcription Voice Assistant")
root.geometry("300x200")

start_btn = tk.Button(root, text="Start Recording", command=start_recording)
start_btn.pack(pady=10)

stop_btn = tk.Button(root, text="Stop Recording", command=stop_recording)
stop_btn.pack(pady=10)

root.mainloop()
