import pyaudio
import wave
from pydub import AudioSegment

# Parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "audio.wav"
MP3_OUTPUT_FILENAME = "audio.mp3"

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Start Recording
stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK)
print("Recording...")

frames = []

for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)

print("Finished recording.")

# Stop Recording
stream.stop_stream()
stream.close()
audio.terminate()

# Save the recorded data as a WAV file
wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(audio.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames))
wf.close()

# Convert WAV to MP3
audio_segment = AudioSegment.from_wav(WAVE_OUTPUT_FILENAME)
audio_segment.export(MP3_OUTPUT_FILENAME, format="mp3")

print(f"Audio saved as {MP3_OUTPUT_FILENAME}")