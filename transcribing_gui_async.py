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
import threading
import queue
import asyncio

# NOT REALLY WORKING WELL

recording = False
transcription_text = ""

audio_chunk_queue = queue.Queue()
transcription_queue = queue.Queue()

def play_sound(file_path):
    try:
        wave_obj = sa.WaveObject.from_wave_file(file_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    except Exception as e:
        print(f"Error playing sound: {e}")

def record_audio_chunks(chunk_duration=1, sample_rate=16000):
    global recording
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=sample_rate, input=True, frames_per_buffer=1024)
    frames = []
    chunk_size = int(sample_rate * chunk_duration)
    try:
        while recording:
            data = stream.read(1024)
            frames.append(data)
            if len(frames) * 1024 >= chunk_size:
                audio_chunk = b''.join(frames)
                audio_chunk_queue.put(audio_chunk)
                frames = []
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

async def transcribe_chunks():
    model = WhisperModel("base", device="cpu", compute_type="int8")
    while recording or not audio_chunk_queue.empty():
        try:
            audio_chunk = audio_chunk_queue.get(timeout=1)
            # Save chunk to temp file
            with wave.open("temp_chunk.wav", 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
                wf.setframerate(16000)
                wf.writeframes(audio_chunk)
            segments, _ = model.transcribe("temp_chunk.wav")
            text = " ".join([segment.text for segment in segments])
            transcription_queue.put(text)
        except queue.Empty:
            await asyncio.sleep(0.1)
    # Clean up temp file
    if os.path.exists("temp_chunk.wav"):
        os.remove("temp_chunk.wav")

def start_async_transcription():
    global recording, transcription_text
    recording = True
    play_sound("audio/start_recording.wav")
    threading.Thread(target=record_audio_chunks).start()
    asyncio.run(transcribe_chunks())
    # Gather all transcriptions
    texts = []
    while not transcription_queue.empty():
        texts.append(transcription_queue.get())
    transcription_text = " ".join(texts)
    pyperclip.copy(transcription_text)
    show_transcription_popup(transcription_text)

def start_recording():
    global recording
    recording = True
    threading.Thread(target=start_async_transcription).start()

def stop_recording():
    global recording
    recording = False
    play_sound("audio/stop_recording.wav")

def show_transcription_popup(text):
    popup = tk.Toplevel(root)
    popup.title("Transcription Result")
    text_field = tk.Text(popup, wrap="word", width=50, height=10)
    text_field.pack(padx=10, pady=10)
    text_field.insert("1.0", text)
    text_field.config(state="disabled")
    tk.Button(popup, text="Close", command=popup.destroy).pack(pady=5)

def copy_to_clipboard():
    pyperclip.copy(transcription_text)
    messagebox.showinfo("Clipboard", "Transcription copied to clipboard!")

# GUI Setup
root = tk.Tk()
root.title("Thelia - Voice Assistant UI")
root.geometry("300x200")

start_btn = tk.Button(root, text="Start Recording", command=start_recording)
start_btn.pack(pady=10)

stop_btn = tk.Button(root, text="Stop Recording", command=stop_recording)
stop_btn.pack(pady=10)

copy_btn = tk.Button(root, text="Copy to Clipboard", command=copy_to_clipboard)
copy_btn.pack(pady=10)

root.mainloop()