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

# User Imports
from logger import Logger

is_recording = False
transcription_text = ""

class Lyra(Logger):
    """
    Lyra GUI Application for Transcription Voice Assistant
    This application allows users to record audio from their microphone,
    transcribe it using the Whisper model, and display the transcription in a popup window.
    It also provides options to copy the transcription to the clipboard.
    Attributes:
        root (tk.Tk): The main application window.
        logger (Logger): Logger instance for logging application events.
    """
    def __init__(self, root):
        self.logger = self.create_logger(name=self.__class__.__name__, log_level="DEBUG")
        self.root = root
        self.root.title("Lyra - Transcription Voice Assistant")
        self.root.geometry("300x200")
        self.root.resizable(False, False)
        self.logger.info("Initializing Lyra GUI")

        self.start_btn = tk.Button(self.root, text="Start Recording", command=self.start_recording)
        self.start_btn.pack(pady=10)

        self.stop_btn = tk.Button(self.root, text="Stop Recording", command=self.stop_recording)
        self.stop_btn.pack(pady=10)

    @staticmethod
    def play_sound(file_path):
        try:
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play_obj = wave_obj.play()
            play_obj.wait_done()
        except Exception as e:
            print(f"Error playing sound: {e}")

    @staticmethod
    def record_audio(file_path="recorded_audio.wav", silence_timeout=20):
        global is_recording
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
        frames = []

        silence_threshold = 300
        silent_duration = 3
        silent_chunk_limit = silence_timeout * (16000 // 1024)

        try:
            while is_recording:
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


    def transcribe_audio(self, audio_file_path):
        self.logger.info(f"Transcribing audio...")
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(audio_file_path)
        transcription = " ".join([segment.text for segment in segments])
        return transcription


    def start_recording(self):
        global is_recording
        if is_recording:
            self.logger.warning("Already recording. Please stop the current recording first.")
            return
        is_recording = True
        self.play_sound("audio/start_recording.wav")
        thread = Thread(target=self.record_process)
        thread.start()
        self.logger.info("Starting recording...")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)


    def stop_recording(self):
        global is_recording
        if not is_recording:
            self.logger.warning("Not currently recording. Nothing to stop.")
            return
        is_recording = False
        self.play_sound("audio/stop_recording.wav")
        self.logger.info("Stopped recording.")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)


    def record_process(self):
        global transcription_text
        audio_path = "temp_recording.wav"
        self.record_audio(audio_path)
        transcription_text = self.transcribe_audio(audio_path)
        pyperclip.copy(transcription_text)
        os.remove(audio_path)
        self.show_transcription_popup(transcription_text)


    def show_transcription_popup(self, text):
        self.logger.info("Displaying transcription popup.")
        popup = tk.Toplevel(self.root)
        popup.title("Transcription Result")
        text_field = tk.Text(popup, wrap="word", width=50, height=10)
        text_field.pack(padx=10, pady=10)
        text_field.insert("1.0", text)
        text_field.config(state="disabled")
        tk.Button(popup, text="Copy to Clipboard", command=self.copy_to_clipboard).pack(pady=5)
        tk.Button(popup, text="Close", command=popup.destroy).pack(pady=5)


    def copy_to_clipboard(self):
        pyperclip.copy(transcription_text)
        self.logger.info("Transcription copied to clipboard.")
        messagebox.showinfo("Clipboard", "Transcription copied to clipboard!")


if __name__ == "__main__":
    root = tk.Tk()
    lyra = Lyra(root)
    root.mainloop()

# pyinstaller build command: pyinstaller --onefile --windowed transcribing_gui.py