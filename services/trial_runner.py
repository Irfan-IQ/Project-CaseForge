import json
from pathlib import Path

from services.gemini_service import generate_json
from services.contradiction_checker import run_verdict
from services.firebase_service import archive_trial
from services.evidence_engine import extract_prolog_facts
from database.db import save_case, save_witnesses, save_evidence, save_verdict


def load_demo(demo_key: str) -> dict:
    path = Path(f'demo_cases/{demo_key}.json')
    return json.loads(path.read_text())


def run_custom_trial(dispute: str) -> dict:

    trial = generate_json(
        "trial_gen",
        dispute=dispute
    )
    
    
    case_data = trial["case"]
    evidence_list = trial["evidence"]
    witnesses = trial["witnesses"]
    lawyers = trial["lawyers"]

    case_id = save_case(dispute, case_data)

    save_evidence(case_id, evidence_list)
    save_witnesses(case_id, witnesses)

    prolog_result = step_run_prolog(
        evidence_list,
        witnesses,
        case_data["defendant"]
    )

    firebase_id = step_archive(
        case_id,
        case_data["title"],
        prolog_result,
        []
    )

    return {
        "case_id": case_id,
        "case": case_data,
        "evidence": evidence_list,
        "witnesses": witnesses,
        "lawyers": lawyers,
        "verdict": prolog_result["verdict"],
        "contradictions": prolog_result["contradictions"],
        "firebase_id": firebase_id,
        "is_demo": False
    }


def step_run_prolog(evidence_list: list, witnesses: list, defendant_name: str) -> dict:
    defendant_atom = defendant_name.lower().replace(' ', '_').replace('-', '_')
    all_facts = extract_prolog_facts(evidence_list, witnesses, defendant_name)
    try:
        return run_verdict(all_facts, defendant_atom)
    except Exception as e:
        return {'verdict': 'undecided', 'contradictions': [], 'error': str(e)}


def step_archive(case_id: int, title: str, prolog_result: dict, cross_exams: list) -> str:
    trial_data = {
        'title': title,
        'verdict': prolog_result['verdict'],
        'contradictions': prolog_result['contradictions'],
        'transcript': json.dumps(cross_exams),
    }
    firebase_id = archive_trial(case_id, trial_data) or ''
    save_verdict(case_id, {**prolog_result, 'firebase_id': firebase_id})
    return firebase_id


def run_demo_trial(demo_key: str) -> dict:
    demo = load_demo(demo_key)
    case_id = save_case(demo['dispute_text'], demo)
    evidence_list = demo.get('pre_generated_evidence', [])
    witnesses = demo.get('pre_generated_witnesses', [])
    save_evidence(case_id, evidence_list)
    save_witnesses(case_id, witnesses)
    prolog_result = step_run_prolog(evidence_list, witnesses, demo.get('defendant', 'defendant'))
    firebase_id = step_archive(case_id, demo['title'], prolog_result, [])
    return {
        'case_id': case_id,
        'title': demo['title'],
        'setting': demo.get('setting', ''),
        'defendant': demo.get('defendant', ''),
        'plaintiff': demo.get('plaintiff', ''),
        'evidence_list': evidence_list,
        'witnesses': witnesses,
        'verdict': prolog_result['verdict'],
        'contradictions': prolog_result['contradictions'],
        'firebase_id': firebase_id,
        'is_demo': True,
        'demo_data': demo,
    }
