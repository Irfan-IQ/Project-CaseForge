import sqlite3
import json
from pathlib import Path

DB_PATH = 'database/verdicts.db'


def init_db():
    Path('database').mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    schema = Path('database/schema.sql').read_text()
    conn.executescript(schema)
    conn.commit()
    conn.close()


def save_case(dispute: str, case_data: dict) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        'INSERT INTO cases (dispute_text, title, setting, defendant, plaintiff) VALUES (?, ?, ?, ?, ?)',
        (
            dispute,
            case_data.get('title', ''),
            case_data.get('setting', ''),
            case_data.get('defendant', ''),
            case_data.get('plaintiff', ''),
        )
    )
    case_id = cur.lastrowid
    conn.commit()
    conn.close()
    return case_id


def save_witnesses(case_id: int, witnesses: list):
    conn = sqlite3.connect(DB_PATH)
    for w in witnesses:
        conn.execute(
            'INSERT INTO witnesses (case_id, name, occupation, personality, alibi_claim, secret) VALUES (?, ?, ?, ?, ?, ?)',
            (
                case_id,
                w.get('name', ''),
                w.get('occupation', ''),
                w.get('personality', ''),
                w.get('alibi_claim', ''),
                w.get('secret', ''),
            )
        )
    conn.commit()
    conn.close()


def save_evidence(case_id: int, evidence_list: list):
    conn = sqlite3.connect(DB_PATH)
    for e in evidence_list:
        conn.execute(
            'INSERT INTO evidence (case_id, description, prolog_fact, evidence_type) VALUES (?, ?, ?, ?)',
            (
                case_id,
                e.get('description', ''),
                e.get('prolog_fact', ''),
                e.get('evidence_type', 'physical'),
            )
        )
    conn.commit()
    conn.close()


def save_verdict(case_id: int, verdict_data: dict) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        'INSERT INTO verdicts (case_id, verdict, contradictions, reasoning, firebase_id) VALUES (?, ?, ?, ?, ?)',
        (
            case_id,
            verdict_data.get('verdict', 'undecided'),
            json.dumps(verdict_data.get('contradictions', [])),
            verdict_data.get('reasoning', ''),
            verdict_data.get('firebase_id', ''),
        )
    )
    verdict_id = cur.lastrowid
    conn.commit()
    conn.close()
    return verdict_id


def get_case(case_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute('SELECT * FROM cases WHERE id = ?', (case_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}
