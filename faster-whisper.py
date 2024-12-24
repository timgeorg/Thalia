from faster_whisper import WhisperModel

model_size = "base.en" # #tiny, base, small, large
print("Loading model...")

# Run on GPU with FP16
# model = WhisperModel(model_size, device="cuda", compute_type="float16")

# or run on GPU with INT8
# model = WhisperModel(model_size, device="cuda", compute_type="int8")
# or run on CPU with INT8

model = WhisperModel(model_size, device="cpu", compute_type="int8")
print("Processing audio file...")
segments, info = model.transcribe("audio.mp3", beam_size=5)

print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))


# New Section

