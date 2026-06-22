import google.generativeai as genai
import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')


def load_prompt(name: str, **kwargs) -> str:
    template = Path(f'prompts/{name}.txt').read_text()
    return template.format(**kwargs)


def generate(prompt_name: str, **kwargs) -> str:
    prompt = load_prompt(prompt_name, **kwargs)
    response = model.generate_content(prompt)
    time.sleep(1)
    return response.text


def generate_json(prompt_name: str, **kwargs) -> dict:
    prompt = load_prompt(prompt_name, **kwargs)
    prompt += '\nRespond ONLY with valid JSON. No markdown backticks, no code blocks, just raw JSON.'
    response = model.generate_content(prompt)
    time.sleep(1)
    raw = response.text.strip()
    raw = raw.strip('`')
    if raw.startswith('json'):
        raw = raw[4:].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find('{')
        if start == -1:
            start = raw.find('[')
        end = raw.rfind('}')
        if end == -1:
            end = raw.rfind(']')
        if start != -1 and end != -1:
            return json.loads(raw[start:end + 1])
        raise
