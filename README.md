# CaseForge / VerdictOS

AI-powered courtroom simulation engine. Submit any dispute — stolen biryani, broken collectible, proxy attendance — and watch a full legal drama unfold: witnesses, evidence, lawyer arguments, and a deterministic Prolog verdict.

> **Powered by Google Gemini API** — the creative intelligence behind every case, witness, and argument generated in VerdictOS. Gemini transforms a one-line dispute into a full courtroom drama.

**Live:** https://verdictos.onrender.com

**Stack:** Python 3.11 · Textual TUI · Flask SSE · **Google Gemini API** · SWI-Prolog · SQLite · Firebase Firestore · Render

---

## Local Setup

### 1. Install SWI-Prolog

```bash
# macOS
brew install swi-prolog

# Ubuntu/Debian
sudo apt install swi-prolog
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and add:
```
GEMINI_API_KEY=your_gemini_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
FIREBASE_CRED_PATH=serviceAccountKey.json   # optional
```

- Gemini key: https://aistudio.google.com
- OpenRouter key: https://openrouter.ai/keys (used as fallback if Gemini fails)

### 4. (Optional) Firebase setup

- Go to console.firebase.google.com → Create project → Firestore Database
- Project Settings → Service Accounts → Generate New Private Key
- Save as `serviceAccountKey.json` in the project root

Firebase is optional — the app runs fully without it.

### 5. Run

**Terminal UI (local):**
```bash
python main.py
```

**Web app (local):**
```bash
python app_web.py
```
Then open http://localhost:5000

---

## Architecture

```
User Input
    │
    ▼
OpenRouter API (single call)
    │  Generates: case + evidence + witnesses + lawyers in one JSON
    ▼
SWI-Prolog verdict engine
    │  Evaluates: opportunity + motive + alibi → guilty / not_guilty / insufficient_evidence
    ▼
Firebase Firestore (archive)
    │
    ▼
Textual TUI  /  Flask SSE web app
```

The LLM generates creative content. Prolog decides the verdict — no hallucinated logic.

---

## Deployment (Render)

The app is deployed on Render using Docker. Set these environment variables in the Render dashboard:

```
GEMINI_API_KEY=...
OPENROUTER_API_KEY=...
```

Render auto-deploys on every push to `main`.

---

## Project Structure

```
main.py                     TUI entry point
app_web.py                  Flask web app with SSE streaming
services/
  gemini_service.py         OpenRouter/Gemini API calls + fallback logic
  trial_runner.py           Trial pipeline (run_custom_trial, demo loader)
  contradiction_checker.py  Python ↔ SWI-Prolog bridge
  evidence_engine.py        Prolog fact extraction from AI output
  firebase_service.py       Firestore archive
prompts/
  trial_gen.txt             Single prompt: generates full trial as one JSON
prolog/
  rules.pl                  Legal axioms (opportunity/motive/alibi → verdict)
  evidence.pl               Runtime facts (overwritten per case)
ui/
  app.py                    Textual App class
  screens.py                CaseInputScreen, TrialScreen, VerdictScreen
  widgets.py                EvidenceBoard widget
database/
  db.py                     SQLite data access layer
demo_cases/                 Pre-seeded JSON scenarios (biryani, spiderman, attendance)
Dockerfile                  Docker build (includes SWI-Prolog)
render.yaml                 Render deployment config
```
