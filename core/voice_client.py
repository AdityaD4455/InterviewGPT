"""
Voice Input (real speech-to-text).

Uses Groq's hosted Whisper endpoint to transcribe audio recorded in the
browser via streamlit-mic-recorder. No local GPU or model download needed
-- the audio bytes go straight to Groq's API and come back as text.

This replaces the "Voice Intelligence Agent" from the original spec's
transcription piece. Confidence/filler-word/speaking-speed analysis on
top of the transcript is a natural next step (see README).
"""
import os
import io
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

WHISPER_MODEL = os.getenv("INTERVIEWGPT_WHISPER_MODEL", "whisper-large-v3-turbo")
_client = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set. Copy .env.example to .env and add your key.")
        _client = Groq(api_key=api_key)
    return _client


def transcribe_audio(audio_bytes: bytes, filename: str = "answer.wav") -> str:
    """
    Transcribe recorded audio to text using Groq's Whisper API.
    audio_bytes: raw audio bytes (wav/mp3/m4a/webm all supported by Groq).
    """
    if not audio_bytes:
        return ""
    client = _get_client()
    file_tuple = (filename, io.BytesIO(audio_bytes))
    result = client.audio.transcriptions.create(
        model=WHISPER_MODEL,
        file=file_tuple,
        response_format="text",
    )
    # response_format="text" returns a plain string in recent SDK versions;
    # fall back to .text if the SDK returns an object instead.
    return result if isinstance(result, str) else getattr(result, "text", "")
