import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from google import genai
from google.genai import types

load_dotenv()

# -----------------------------
# Gemini Setup
# -----------------------------
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = "gemini-2.0-flash"

# -----------------------------
# OpenRouter Setup
# -----------------------------
openrouter_client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

# Change this if you want another model
OPENROUTER_MODEL = "meta-llama/llama-3.1-8b-instruct:free"


def load_prompt(name: str, **kwargs) -> str:
    template = Path(f"prompts/{name}.txt").read_text()
    return template.format(**kwargs)


def call_openrouter(prompt: str) -> str:
    response = openrouter_client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content


def generate(prompt_name: str, **kwargs) -> str:
    prompt = load_prompt(prompt_name, **kwargs)

    try:
        response = gemini_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        time.sleep(1)
        return response.text

    except Exception as e:
        try:
            result = call_openrouter(prompt)
            time.sleep(1)
            return result
        except Exception:
            raise


def generate_json(prompt_name: str, **kwargs) -> dict:
    prompt = load_prompt(prompt_name, **kwargs)
    prompt += (
        "\nRespond ONLY with valid JSON. "
        "No markdown backticks, no code blocks, just raw JSON."
    )

    try:
        response = gemini_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        raw = response.text.strip()

    except Exception as e:
        print(f"[WARNING] Gemini failed ({type(e).__name__}: {e}), switching to OpenRouter")
        raw = call_openrouter(prompt).strip()

    raw = raw.strip("`")

    if raw.startswith("json"):
        raw = raw[4:].strip()

    try:
        return json.loads(raw)

    except json.JSONDecodeError:
        start = raw.find("{")
        if start == -1:
            start = raw.find("[")

        end = raw.rfind("}")
        if end == -1:
            end = raw.rfind("]")

        if start != -1 and end != -1:
            return json.loads(raw[start:end + 1])

        raise
