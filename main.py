import os
import uuid
import tempfile

import yt_dlp
import ffmpeg

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator


# ==================================================
# App Config
# ==================================================

app = FastAPI(title="YT Transcriber AI")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ==================================================
# Load Model (chỉ load 1 lần khi startup)
# ==================================================

model = None


@app.on_event("startup")
def load_model():
    global model

    print("🚀 Loading Faster-Whisper model...")

    model = WhisperModel(
        "small",           # base | small | medium | large
        device="cuda",     # nếu lỗi CUDA → đổi thành "cpu"
        compute_type="float16"
    )

    print("✅ Model loaded successfully!")


# ==================================================
# Routes
# ==================================================

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.post("/process")
async def process(
    url: str = Form(...),
    target_lang: str = Form("vi")
):
    file_id = str(uuid.uuid4())

    with tempfile.TemporaryDirectory() as temp_dir:

        # 1️⃣ Download audio
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(temp_dir, f"{file_id}.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
            }],
            "quiet": True,
            "noplaylist": True,
            "js_runtimes": {"node": {}}
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        mp3_path = os.path.join(temp_dir, f"{file_id}.mp3")
        wav_path = os.path.join(temp_dir, f"{file_id}.wav")

        # 2️⃣ Convert to wav mono 16kHz
        (
            ffmpeg
            .input(mp3_path)
            .output(wav_path, ac=1, ar="16000")
            .overwrite_output()
            .run(quiet=True)
        )

        # 3️⃣ Transcribe
        segments, info = model.transcribe(wav_path)

        original_text = " ".join([seg.text for seg in segments])
        detected_language = info.language

        # 4️⃣ Translate
        translated_text = GoogleTranslator(
            source="auto",
            target=target_lang
        ).translate(original_text)

    return JSONResponse({
        "detected_language": detected_language,
        "original_text": original_text.strip(),
        "translated_text": translated_text,
        "target_language": target_lang
    })


# ==================================================
# Run with: python main.py
# ==================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=7000,
        reload=False,
        log_level="info"
    )
