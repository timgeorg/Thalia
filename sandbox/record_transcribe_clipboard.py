import pyaudio
import wave
import numpy as np
import os
import pyperclip
import keyboard
import time
import simpleaudio as sa
from faster_whisper import WhisperModel


def play_sound(file_path):
    try:
        wave_obj = sa.WaveObject.from_wave_file(file_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    except Exception as e:
        print(f"Error playing sound: {e}")


def wait_for_button_press(key='space'):
    print(f"Press '{key.upper()}' to start recording, or 'Q' to quit.")
    while True:
        if keyboard.is_pressed('q'):
            return False
        if keyboard.is_pressed(key):
            while keyboard.is_pressed(key):  # Debounce
                time.sleep(0.1)
            return True
        time.sleep(0.1)


def record_audio(file_path="recorded_audio.wav", silence_timeout=20):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
    frames = []

    print("Recording... Press SPACE again to stop.")
    start_time = time.time()
    silence_threshold = 300
    silent_duration = 3
    silent_chunk_limit = silence_timeout * (16000 // 1024)

    try:
        while True:
            data = stream.read(1024)
            frames.append(data)

            audio_data = np.frombuffer(data, dtype=np.int16)
            if np.abs(audio_data).mean() < silence_threshold:
                silent_duration += 1
            else:
                silent_duration = 0

            if keyboard.is_pressed('space'):
                while keyboard.is_pressed('space'):
                    time.sleep(0.1)
                print("Button press detected. Stopping recording.")
                break

            if silent_duration > silent_chunk_limit:
                print("Silence timeout reached. Stopping recording.")
                break

    except KeyboardInterrupt:
        print("Recording interrupted.")

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


def main():
    start_sound = "audio/start_recording.wav"
    stop_sound = "audio/stop_recording.wav"
    print("Welcome! Press SPACE to record, Q to quit.\n")

    while True:
        if not wait_for_button_press('space'):
            print("Goodbye!")
            break

        play_sound(start_sound)
        audio_path = "temp_recording.wav"
        record_audio(audio_path)
        play_sound(stop_sound)  

        transcription = transcribe_audio(audio_path)
        pyperclip.copy(transcription)
        print("📋 Transcription copied to clipboard.\n")

        os.remove(audio_path)


if __name__ == "__main__":
    main()
