import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import re

load_dotenv()

from google import genai as google_genai

gemini_client = google_genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = "gemini-2.0-flash-lite"

openrouter_client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

OPENROUTER_MODELS = [
    "google/gemma-4-26b-a4b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
]


def load_prompt(name: str, **kwargs) -> str:
    template = Path(f"prompts/{name}.txt").read_text()
    for key, value in kwargs.items():
        template = template.replace(f"{{{key}}}", str(value))
    return template


def _call_openrouter(prompt: str) -> str:
    last_error = None
    for model in OPENROUTER_MODELS:
        try:
            response = openrouter_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                timeout=60,
            )
            print(f"[OpenRouter OK] {model}")
            return response.choices[0].message.content
        except Exception as e:
            print(f"[OpenRouter FAIL] {model}: {e}")
            last_error = e
            time.sleep(2)
    raise RuntimeError(f"OpenRouter fallback exhausted. Last: {last_error}")


def generate(prompt_name: str, **kwargs) -> str:
    prompt = load_prompt(prompt_name, **kwargs)
    try:
        response = gemini_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        print("[Gemini OK]")
        return response.text
    except Exception as e:
        print(f"[Gemini FAIL] {e}")
        return _call_openrouter(prompt)


def generate_json(prompt_name: str, **kwargs) -> dict:
    prompt = load_prompt(prompt_name, **kwargs)
    prompt += "\nRespond ONLY with valid JSON. No markdown. No explanations."

    raw = None
    gemini_error = None

    try:
        response = gemini_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        raw = response.text.strip()
        print("[Gemini OK]")
    except Exception as e:
        gemini_error = e
        print(f"[Gemini FAIL] {e}")

    if raw is None:
        raw = _call_openrouter(prompt).strip()

    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw).strip()
    if raw.lower().startswith("json"):
        raw = raw[4:].strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        if start == -1:
            start = raw.find("[")
        end = max(raw.rfind("}"), raw.rfind("]"))
        if start != -1 and end != -1:
            return json.loads(raw[start:end + 1])
        raise
