import google.generativeai as genai
import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import re

load_dotenv()

# -----------------------------
# Gemini Setup
# -----------------------------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-2.5-flash")

# -----------------------------
# OpenRouter Setup
# -----------------------------
openrouter_client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

# Change this if you want another model
OPENROUTER_MODEL = "google/gemma-4-26b-a4b-it:free"


def load_prompt(name: str, **kwargs) -> str:
    template = Path(f"prompts/{name}.txt").read_text()

    for key, value in kwargs.items():
        template = template.replace(
            f"{{{key}}}",
            str(value)
        )

    return template


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
        response = gemini_model.generate_content(prompt)
        time.sleep(1)
        return response.text

    except Exception as e:

        try:
            result = call_openrouter(prompt)
            time.sleep(1)
            return result

        except Exception as fallback_error:
            raise


def generate_json(prompt_name: str, **kwargs) -> dict:
    prompt = load_prompt(prompt_name, **kwargs)
    gemini_error = None

    prompt += (
        "\nRespond ONLY with valid JSON. "
        "No markdown. No explanations."
    )

    raw = None

    # -----------------------------
    # Gemini First
    # -----------------------------
    try:
        response = gemini_model.generate_content(prompt)
        raw = response.text.strip()

    except Exception as e:
        gemini_error = e
        print(f"[Gemini Failed] {e}")

    # -----------------------------
    # OpenRouter Fallback
    # -----------------------------
    if raw is None:

        try:
            print("[Fallback] Using OpenRouter")

            raw = call_openrouter(prompt).strip()

        except Exception as fallback_error:
            print("Gemini Error =", gemini_error)
            raise RuntimeError(
                    f"Gemini and OpenRouter both failed.\n"
                    f"Gemini: {gemini_error}\n"
                    f"OpenRouter: {fallback_error}"
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
