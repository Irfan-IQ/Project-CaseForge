import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import re

load_dotenv()

# -----------------------------
# OpenRouter — primary + fallback
# -----------------------------
openrouter_client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

PRIMARY_MODEL = "google/gemini-2.0-flash-exp:free"
FALLBACK_MODEL = "mistralai/mistral-7b-instruct:free"


def load_prompt(name: str, **kwargs) -> str:
    template = Path(f"prompts/{name}.txt").read_text()

    for key, value in kwargs.items():
        template = template.replace(
            f"{{{key}}}",
            str(value)
        )

    return template


def call_model(prompt: str, model: str) -> str:
    response = openrouter_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


def generate(prompt_name: str, **kwargs) -> str:
    prompt = load_prompt(prompt_name, **kwargs)

    try:
        result = call_model(prompt, PRIMARY_MODEL)
        time.sleep(1)
        return result
    except Exception:
        result = call_model(prompt, FALLBACK_MODEL)
        time.sleep(1)
        return result


def generate_json(prompt_name: str, **kwargs) -> dict:
    prompt = load_prompt(prompt_name, **kwargs)

    prompt += (
        "\nRespond ONLY with valid JSON. "
        "No markdown. No explanations."
    )

    raw = None
    primary_error = None

    try:
        raw = call_model(prompt, PRIMARY_MODEL).strip()
        print(f"[Primary] {PRIMARY_MODEL} succeeded")
    except Exception as e:
        primary_error = e
        print(f"[Primary Failed] {e}")

    if raw is None:
        try:
            print(f"[Fallback] Trying {FALLBACK_MODEL}")
            raw = call_model(prompt, FALLBACK_MODEL).strip()
        except Exception as fallback_error:
            raise RuntimeError(
                f"Both models failed.\n"
                f"Primary: {primary_error}\n"
                f"Fallback: {fallback_error}"
            )

    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw.strip())
    if raw.lower().startswith("json"):  # bare "json" prefix fallback
        raw = raw[4:].strip()
    raw = raw.strip()

    try:
        return json.loads(raw)

    except json.JSONDecodeError:

        start = raw.find("{")
        if start == -1:
            start = raw.find("[")

        end = max(
            raw.rfind("}"),
            raw.rfind("]")
        )

        if start != -1 and end != -1:
            return json.loads(
                raw[start:end + 1]
            )

        raise
