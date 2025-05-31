import sounddevice as sd
import numpy as np
import wave

duration = 10  # seconds
samplerate = 48000
channels = 2  # Stereo recording

# List devices to find WASAPI loopback
print(sd.query_devices())


# print("Available input devices:")
# for idx, dev in enumerate(sd.query_devices()):
#     if dev['max_input_channels'] > 0:
#         print(f"Index: {idx}, Name: {dev['name']}, Channels: {dev['max_input_channels']}, SR: {dev['default_samplerate']}")

# # Replace with the index of your loopback device
# device_index = 27

# recording = sd.rec(
#     int(samplerate * duration), 
#     samplerate=samplerate,
#     channels=channels, 
#     dtype='int16', 
#     device=device_index
#     )
# sd.wait()

# # Save as WAV file
# with wave.open("desktop_output.wav", 'wb') as wf:
#     wf.setnchannels(channels)
#     wf.setsampwidth(2)  # 16 bits
#     wf.setframerate(samplerate)
#     wf.writeframes(recording.tobytes())


import soundcard as sc
import soundfile as sf
import warnings

# https://github.com/bastibe/SoundCard/issues/166
# Suppress the SoundcardRuntimeWarning
warnings.filterwarnings("ignore", category=sc.SoundcardRuntimeWarning)


OUTPUT_FILE_NAME = "out_bass.wav"    # file name.
SAMPLE_RATE = 48000              # [Hz]. sampling rate.
RECORD_SEC = 5                  # [sec]. duration recording audio.

with sc.get_microphone(id=str(sc.default_speaker().name), include_loopback=True).recorder(samplerate=SAMPLE_RATE) as mic:
    # record audio with loopback from default speaker.
    data = mic.record(numframes=SAMPLE_RATE*RECORD_SEC)
    
    # change "data=data[:, 0]" to "data=data", if you would like to write audio as multiple-channels.
    sf.write(file=OUTPUT_FILE_NAME, data=data[:, 0], samplerate=SAMPLE_RATE)