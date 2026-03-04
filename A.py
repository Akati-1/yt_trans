from faster_whisper import WhisperModel

model = WhisperModel(
    "small",
    device="cuda",
    compute_type="int8_float16"
)

print("GPU OK")
