import openai
import wave
import pyaudio
import os
import torch
import sys

import ollama
import asyncio
from ollama import AsyncClient

from faster_whisper import WhisperModel

sys.path.append(os.path.join(os.path.dirname(__file__), 'OpenVoice'))
from openvoice import se_extractor
from openvoice.api import BaseSpeakerTTS, ToneColorConverter
import subprocess


# Constants for colored text
NEON_GREEN = '\033[92m'
PINK = '\033[95m'
CYAN = '\033[96m'
RESET_COLOR = '\033[0m'

def open_file(file_path):
    with open(file_path, "r") as file:
        return file.read()
    

# client = openai.OpenAI(base_url="http://127.0.0.1:11434", api_key="not-needed")
chat_log_filename = "chat_log.txt"

# Function to play audio using PyAudio
def play_audio(file_path):
    # Open the audio file
    wf = wave.open(file_path, 'rb')

    # Create a PyAudio instance
    p = pyaudio.PyAudio()

    # Open a stream to play audio
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    # Read and play audio data
    data = wf.readframes(1024)
    while data:
        stream.write(data)
        data = wf.readframes(1024)

    # Close the stream and terminate PyAudio
    stream.stop_stream()
    stream.close()
    p.terminate()



# Model and device setup
ckpt_base = 'OpenVoice/checkpoints/base_speakers/EN'
ckpt_converter = 'OpenVoice/checkpoints/converter'
device="cuda:0" if torch.cuda.is_available() else "cpu"
print("DEVICE:", device)
output_dir = 'outputs'
base_speaker_tts = BaseSpeakerTTS(f'{ckpt_base}/config.json', device=device)
base_speaker_tts.load_ckpt(f'{ckpt_base}/checkpoint.pth')
tone_color_converter = ToneColorConverter(f'{ckpt_converter}/config.json', device=device)
tone_color_converter.load_ckpt(f'{ckpt_converter}/checkpoint.pth')
os.makedirs(output_dir, exist_ok=True)

source_se = torch.load(f'{ckpt_base}/en_default_se.pth', weights_only=True).to(device)
reference_speaker = 'Openvoice/resources/dualipa_reference.mp3' # This is the voice you want to clone
target_se, audio_name = se_extractor.get_se(reference_speaker, tone_color_converter, target_dir='processed', vad=True)

save_path = f'{output_dir}/output.wav'
src_path = f'{output_dir}/tmp.wav'

play_audio("audio/startup.wav")

# Main processing function
async def process_text(prompt, style):
    # Process text and generate audio
    try:
        base_speaker_tts.tts(prompt, src_path, speaker=style, language='English', speed=1.1)

        # Run the tone color converter
        encode_message = "@MyShell"
        tone_color_converter.convert(
            audio_src_path=src_path, 
            src_se=source_se, 
            tgt_se=target_se, 
            output_path=save_path, 
            message=encode_message
        )
        print("Audio generated successfully.")
        return save_path


    except Exception as e:
        print(f"Error during audio generation: {e}")
        return None


async def play_audio_async(file_path):
    # Open the audio file
    wf = wave.open(file_path, 'rb')

    # Create a PyAudio instance
    p = pyaudio.PyAudio()

    # Open a stream to play audio
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    # Read and play audio data
    data = wf.readframes(1024)
    while data:
        stream.write(data)
        data = wf.readframes(1024)

    # Close the stream and terminate PyAudio
    stream.stop_stream()
    stream.close()
    p.terminate()


async def process_and_play(prompt, style):
    save_path = await process_text(prompt, style)
    if save_path:
        await play_audio_async(save_path)

def chatgpt_streamed(user_input, system_message, conversation_history, bot_name):
    messages = [{"role": "system", "content": system_message}] + conversation_history + [{"role": "user", "content": user_input}]
    temperature = 1

    response = ollama.chat(
        model="llama3.2",
        messages=messages,
    )
    streamed_completion = response["message"]["content"]

    return streamed_completion

async def chatgpt_async(user_input, system_message, conversation_history, bot_name):
    messages = [{"role": "system", "content": system_message}] + conversation_history + [{"role": "user", "content": user_input}]
    temperature = 1

    full_content = ""
    partial_content = ""

    async for part in await AsyncClient().chat(
        model="llama3.2",
        messages=messages,
        stream=True,
    ):
        content = part["message"]["content"]
        print(content, end="", flush=True)
        full_content += content
        partial_content += content

        if any(content.endswith(punct) for punct in ['.', '!', '?']) and len(partial_content) > 400:
            await process_and_play(partial_content, style="default")
            partial_content = ""

    # Ensure any remaining partial content is processed
    await process_and_play(partial_content, style="default")

    return full_content


def transcribe_with_whisper(audio_file_path):
    # Load the model
    model_size = "base"
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    # Transcribe audio
    segments, info = model.transcribe(audio_file_path)
    print(segments)
    transcription = " ".join([segment.text for segment in segments])
    print("Transcription:", transcription)
    return transcription

def record_audio(file_path):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
    frames = []

    print("Recording audio...")

    try:
        while True:
            data = stream.read(1024)
            frames.append(data)
    except KeyboardInterrupt:
        pass
    print("Recording stopped.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(file_path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(16000)
    wf.writeframes(b''.join(frames))
    wf.close()


async def user_chatbot_conversation():
    conversation_history = []
    system_message = open_file("system_message.txt")
    
    while True:
        play_audio("audio/start_recording.wav")
        audio_file = "temp_recoding.wav"
        record_audio(audio_file)
        play_audio("audio/stop_recording.wav")
        user_input = transcribe_with_whisper(audio_file)
        os.remove(audio_file)

        if "exit" in user_input.lower():
            break

        print(CYAN + "You:", user_input + RESET_COLOR)
        conversation_history.append({"role": "user", "content": user_input})
        print(PINK + "Thalia" + RESET_COLOR)
        chatbot_response = await chatgpt_async(user_input, system_message, conversation_history, "Thalia")
        conversation_history.append({"role": "assistant", "content": chatbot_response})

        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]


asyncio.run(user_chatbot_conversation())
