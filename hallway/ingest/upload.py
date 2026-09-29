"""Upload page for the presenting laptop: drop a .wav or .txt, it lands in the inbox as text.

Runs next to Desk, never on the VM. Audio is transcribed here with faster-whisper and
discarded; only the transcript is written to the inbox directory Desk watches.
"""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from hallway.ingest.transcribe import transcribe

INBOX = Path(os.getenv("SAFESCRIBE_INBOX", "inbox"))
MAX_BYTES = 25 * 1024 * 1024
app = FastAPI(title="Safe Scribe upload", docs_url=None, redoc_url=None)

PAGE = """<!doctype html><meta charset="utf-8"><title>Safe Scribe upload</title>
<style>body{font:16px system-ui;margin:3rem auto;max-width:40rem;padding:0 1rem}
form{border:2px dashed #888;padding:2rem;border-radius:12px}</style>
<h1>Safe Scribe</h1><p>Drop a shift-handoff recording (.wav) or transcript (.txt). Synthetic patients only.
Audio is transcribed on this laptop and discarded; only text enters the Band case room.</p>
<form method="post" action="/upload" enctype="multipart/form-data">
<input type="file" name="file" accept=".wav,.txt,.md" required> <button>Send to Desk</button></form>"""


def _safe_stem(name: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_-]", "_", Path(name or "recording").stem)[:80]
    return stem or "recording"


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return PAGE


@app.post("/upload")
async def upload(file: UploadFile = File(...)) -> JSONResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".wav", ".txt", ".md"):
        raise HTTPException(status_code=415, detail="only .wav, .txt or .md")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="empty upload")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="file too large")
    INBOX.mkdir(parents=True, exist_ok=True)
    target = INBOX / f"{_safe_stem(file.filename)}.txt"
    meta: dict = {"source": "text"}
    if suffix == ".wav":
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
            tmp.write(data); tmp.flush()
            result = transcribe(tmp.name)
        text = result["transcript"]
        meta = {"source": "wav", "audio_seconds": result["audio_seconds"], "model": result["model"],
                "elapsed_seconds": result["elapsed_seconds"], "audio_left_machine_bytes": 0}
    else:
        text = data.decode("utf-8", errors="replace")
    if not text.strip():
        raise HTTPException(status_code=422, detail="nothing transcribed")
    target.write_text(text.strip() + "\n", encoding="utf-8")
    return JSONResponse({"inbox_file": str(target), "chars": len(text.strip()), **meta})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("SAFESCRIBE_UPLOAD_PORT", "8010")))
