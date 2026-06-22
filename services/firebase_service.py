import os
import firebase_admin
from firebase_admin import credentials, firestore

_db = None


def get_db():
    global _db
    if _db is not None:
        return _db

    cred_path = os.getenv('FIREBASE_CRED_PATH')
    if not cred_path or not os.path.exists(cred_path):
        print('[Firebase] WARNING: serviceAccountKey.json not found. Firebase disabled.')
        return None

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    _db = firestore.client()
    return _db


def archive_trial(case_id: int, trial_data: dict) -> str | None:
    db = get_db()
    if db is None:
        return None

    doc_ref = db.collection('trials').add({
        'case_id': case_id,
        'title': trial_data.get('title', ''),
        'verdict': trial_data.get('verdict', ''),
        'contradictions': trial_data.get('contradictions', []),
        'transcript': trial_data.get('transcript', ''),
        'timestamp': firestore.SERVER_TIMESTAMP,
    })
    return doc_ref[1].id


def get_recent_trials(limit: int = 10) -> list | None:
    db = get_db()
    if db is None:
        return None

    docs = (
        db.collection('trials')
        .order_by('timestamp', direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    return [doc.to_dict() | {'id': doc.id} for doc in docs]
