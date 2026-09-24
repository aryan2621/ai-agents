import os
import tempfile

import speech_recognition as sr
from fastapi import APIRouter, File, Header, HTTPException, UploadFile

router = APIRouter(prefix="/speech", tags=["speech"])


def _extract_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return authorization[7:]


@router.post("/transcribe")
async def transcribe_speech(
    audio: UploadFile = File(...),
    authorization: str | None = Header(default=None),
) -> dict[str, str]:
    _extract_bearer(authorization)

    if not audio.content_type or not (
        audio.content_type.startswith("audio/") or audio.content_type == "application/octet-stream"
    ):
        raise HTTPException(status_code=400, detail="Expected an audio file")

    data = await audio.read()
    if len(data) <= 44:
        raise HTTPException(status_code=400, detail="Recording is empty")

    suffix = ".wav" if "wav" in (audio.content_type or "") else ".wav"
    tmp_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        recognizer = sr.Recognizer()
        with sr.AudioFile(tmp_path) as source:
            recorded = recognizer.record(source)

        try:
            text = recognizer.recognize_google(recorded)
        except sr.UnknownValueError:
            return {"text": ""}
        except sr.RequestError as exc:
            raise HTTPException(
                status_code=503,
                detail="Speech transcription unavailable. Check your internet connection.",
            ) from exc

        return {"text": text.strip()}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
