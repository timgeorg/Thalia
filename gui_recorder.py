import tkinter as tk
import threading
import wave
import pyaudio
import numpy as np
import pyperclip
import os
from faster_whisper import WhisperModel
import simpleaudio as sa

class AudioTranscriberApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Recorder")
        self.is_recording = False
        self.frames = []
        self.transcription = ""
        self.audio_path = "gui_temp_audio.wav"

        # Buttons
        self.start_btn = tk.Button(root, text="Start Recording", command=self.start_recording)
        self.start_btn.pack(pady=10)

        self.stop_btn = tk.Button(root, text="Stop Recording", command=self.stop_recording, state=tk.DISABLED)
        self.stop_btn.pack(pady=10)

        self.copy_btn = tk.Button(root, text="Copy to Clipboard", command=self.copy_to_clipboard, state=tk.DISABLED)
        self.copy_btn.pack(pady=10)

    def play_sound(self, file_path):
        try:
            sa.WaveObject.from_wave_file(file_path).play()
        except Exception as e:
            print("Error playing sound:", e)

    def start_recording(self):
        self.is_recording = True
        self.frames = []
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.copy_btn.config(state=tk.DISABLED)

        self.play_sound("audio/start_recording.wav")

        threading.Thread(target=self.record_audio).start()

    def record_audio(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)

        print("Recording...")
        silence_threshold = 300
        silence_chunk_limit = 20 * (16000 // 1024)
        silent_chunks = 0

        while self.is_recording:
            data = self.stream.read(1024)
            self.frames.append(data)

            audio_data = np.frombuffer(data, dtype=np.int16)
            if np.abs(audio_data).mean() < silence_threshold:
                silent_chunks += 1
            else:
                silent_chunks = 0

            if silent_chunks > silence_chunk_limit:
                print("Silence timeout reached. Auto-stopping.")
                self.stop_recording()
                break

        print("Stopped recording.")

    def stop_recording(self):
        if not self.is_recording:
            return

        self.is_recording = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

        self.play_sound("audio/stop_recording.wav")

        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

        with wave.open(self.audio_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(b''.join(self.frames))

        self.transcribe_audio()
        self.copy_btn.config(state=tk.NORMAL)

    def transcribe_audio(self):
        print("Transcribing...")
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(self.audio_path)
        self.transcription = " ".join([seg.text for seg in segments])
        print("Transcription:", self.transcription)

    def copy_to_clipboard(self):
        if self.transcription:
            pyperclip.copy(self.transcription)
            print("Copied to clipboard.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioTranscriberApp(root)
    root.mainloop()
