"""
Thin wrapper around the Groq API used by every agent in InterviewGPT Pro.

All agents call `ask_json()` or `ask_text()` instead of touching the SDK
directly, so the model name, retries, and JSON-parsing logic live in one
place. Groq's API is OpenAI-compatible chat completions (very fast, free
tier available at console.groq.com).
"""
import os
import json
import re
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("INTERVIEWGPT_MODEL") or st.secrets.get("INTERVIEWGPT_MODEL", "llama-3.3-70b-versatile")
_client = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            api_key = st.secrets.get("GROQ_API_KEY", None)
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY not found. Configure it in .env locally or Streamlit Secrets."
            )
        _client = Groq(api_key=api_key)
    return _client


def ask_text(system: str, user: str, max_tokens: int = 1200, temperature: float = 0.4) -> str:
    """Send a system+user prompt, return the raw text response."""
    client = _get_client()
    resp = client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return (resp.choices[0].message.content or "").strip()


def ask_json(system: str, user: str, max_tokens: int = 1500, temperature: float = 0.3) -> dict:
    """
    Send a system+user prompt that instructs the model to return ONLY JSON,
    then parse and return it as a dict. Falls back to extracting a {...}
    block if the model wraps the JSON in prose or code fences.
    """
    strict_system = (
        system
        + "\n\nCRITICAL: Respond with ONLY valid JSON. No markdown code "
        "fences, no preamble, no explanation before or after the JSON."
    )
    client = _get_client()
    resp = client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": strict_system},
            {"role": "user", "content": user},
        ],
    )
    raw = (resp.choices[0].message.content or "").strip()
    cleaned = re.sub(r"^```(json)?|```$", "", raw, flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError(f"Model did not return parseable JSON:\n{raw}")
