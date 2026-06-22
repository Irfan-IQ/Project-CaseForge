CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dispute_text TEXT NOT NULL,
    title TEXT,
    setting TEXT,
    defendant TEXT,
    plaintiff TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS witnesses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER REFERENCES cases(id),
    name TEXT,
    occupation TEXT,
    personality TEXT,
    alibi_claim TEXT,
    secret TEXT
);

CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER REFERENCES cases(id),
    description TEXT,
    prolog_fact TEXT,
    evidence_type TEXT
);

CREATE TABLE IF NOT EXISTS verdicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER REFERENCES cases(id),
    verdict TEXT,
    contradictions TEXT,
    reasoning TEXT,
    firebase_id TEXT
);
