# CaseForge / VerdictOS

AI-powered courtroom simulation engine. Submit any dispute — stolen biryani, broken collectible, proxy attendance — and watch a full legal drama unfold: witnesses, evidence, lawyer arguments, cross-examinations, and a deterministic Prolog verdict.

**Stack:** Python 3.11 · Textual TUI · Gemini 1.5-flash · SWI-Prolog · SQLite · Firebase Firestore · Google Cloud Run

---

## Local Setup

### 1. Install SWI-Prolog (required before pip install)

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
GEMINI_API_KEY=your_key_here
FIREBASE_CRED_PATH=serviceAccountKey.json   # optional
```

Get a Gemini API key at: https://aistudio.google.com

### 4. (Optional) Firebase setup

- Go to console.firebase.google.com → Create project → Firestore Database
- Project Settings → Service Accounts → Generate New Private Key
- Save the file as `serviceAccountKey.json` in the project root
- Add `FIREBASE_CRED_PATH=serviceAccountKey.json` to `.env`

Firebase is optional — the app runs fully without it.

### 5. Run

```bash
python main.py
```

---

## Usage

- Type any dispute into the input field and press **FILE CASE**
- Or use the demo buttons (Biryani Theft, SpiderMan, Attendance Fraud) for instant pre-seeded trials
- Press **q** to quit at any time

---

## Architecture

```
User Input → Gemini (case gen) → Gemini (evidence) → Gemini (witnesses)
          → Gemini (lawyer args) → Gemini (cross-exam)
          → SWI-Prolog (deterministic verdict)
          → Firebase (archive) → Textual UI (display)
```

The LLM generates creative content. Prolog decides the verdict — no hallucinated logic.

---

## Google Cloud Run Deployment

```bash
# One-time setup
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com

# Deploy
gcloud run deploy verdictos \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_key_here
```

---

## Project Structure

```
main.py                     Entry point
services/
  gemini_service.py         Gemini API calls
  trial_runner.py           Pipeline step functions
  contradiction_checker.py  Python ↔ Prolog bridge
  evidence_engine.py        Prolog fact extraction
  firebase_service.py       Firestore archive
prompts/                    Gemini prompt templates
prolog/
  rules.pl                  Legal axioms (guilty/contradiction/verdict)
  evidence.pl               Runtime facts (overwritten per case)
  judge.pl                  Entry predicate
ui/
  app.py                    Textual App class
  screens.py                CaseInputScreen, TrialScreen, VerdictScreen
  widgets.py                EvidenceBoard widget
  assets/theme.tcss         Dark theme stylesheet
database/
  schema.sql                SQLite schema
  db.py                     Data access layer
demo_cases/                 Pre-seeded JSON scenarios
deployment/                 Dockerfile + Cloud Build config
```
