import google.generativeai as genai
import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

print(f"[STARTUP] GEMINI_API_KEY present: {bool(GEMINI_API_KEY)}")
print(f"[STARTUP] OPENROUTER_API_KEY present: {bool(OPENROUTER_API_KEY)}")

genai.configure(api_key=GEMINI_API_KEY)

GEMINI_MODELS = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-latest"]

OPENROUTER_MODELS = [
    "deepseek/deepseek-r1:free",
    "deepseek/deepseek-chat:free",
    "microsoft/phi-3-mini-128k-instruct:free",
    "qwen/qwen-2-7b-instruct:free",
]

openrouter_client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)


def load_prompt(name: str, **kwargs) -> str:
    template = Path(f"prompts/{name}.txt").read_text()
    return template.format(**kwargs)


def call_gemini(prompt: str) -> str:
    for model_name in GEMINI_MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            print(f"[OK] Gemini succeeded with {model_name}")
            time.sleep(1)
            return response.text
        except Exception as e:
            print(f"[WARN] Gemini {model_name} failed: {type(e).__name__}: {e}")
    raise RuntimeError("All Gemini models failed")


def call_openrouter(prompt: str) -> str:
    for model_name in OPENROUTER_MODELS:
        try:
            response = openrouter_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            print(f"[OK] OpenRouter succeeded with {model_name}")
            time.sleep(1)
            return response.choices[0].message.content
        except Exception as e:
            print(f"[WARN] OpenRouter {model_name} failed: {type(e).__name__}: {e}")
    raise RuntimeError("All OpenRouter models failed")


def call_ai(prompt: str) -> str:
    try:
        return call_gemini(prompt)
    except Exception as e:
        print(f"[INFO] Gemini exhausted, trying OpenRouter: {e}")
        return call_openrouter(prompt)


def generate(prompt_name: str, **kwargs) -> str:
    prompt = load_prompt(prompt_name, **kwargs)
    return call_ai(prompt)


def generate_json(prompt_name: str, **kwargs) -> dict:
    prompt = load_prompt(prompt_name, **kwargs)
    prompt += "\nRespond ONLY with valid JSON. No markdown backticks, no code blocks, just raw JSON."

    raw = call_ai(prompt).strip()

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
