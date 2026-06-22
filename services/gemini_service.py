import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import re

load_dotenv()

openrouter_client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

MODELS = [
    "google/gemma-4-26b-a4b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "liquid/lfm-2.5-1.2b-instruct:free",
]


def load_prompt(name: str, **kwargs) -> str:
    template = Path(f"prompts/{name}.txt").read_text()
    for key, value in kwargs.items():
        template = template.replace(f"{{{key}}}", str(value))
    return template


def _call(prompt: str) -> str:
    last_error = None
    for model in MODELS:
        try:
            response = openrouter_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                timeout=60,
            )
            print(f"[OK] {model}")
            return response.choices[0].message.content
        except Exception as e:
            print(f"[FAIL] {model}: {e}")
            last_error = e
            time.sleep(2)
    raise RuntimeError(f"All models failed. Last error: {last_error}")


def generate(prompt_name: str, **kwargs) -> str:
    return _call(load_prompt(prompt_name, **kwargs))


def generate_json(prompt_name: str, **kwargs) -> dict:
    prompt = load_prompt(prompt_name, **kwargs)
    prompt += "\nRespond ONLY with valid JSON. No markdown. No explanations."

    raw = _call(prompt).strip()

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
