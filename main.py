import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from database.db import init_db, save_case, save_witnesses, save_evidence, save_verdict
from services.gemini_service import generate_json
from services.contradiction_checker import run_verdict
from services.firebase_service import archive_trial
from services.evidence_engine import extract_prolog_facts
from ui.app import VerdictOSApp


def run_trial(
    dispute: str,
    demo_key: str | None,
    log_fn=None,
    status_fn=None,
) -> dict:
    def log(msg: str, style: str = 'white') -> None:
        if log_fn:
            log_fn(msg, style)

    def status(msg: str) -> None:
        if status_fn:
            status_fn(msg)

    if demo_key:
        demo_path = Path(f'demo_cases/{demo_key}.json')
        demo = json.loads(demo_path.read_text())
        dispute = demo['dispute_text']

        log(f'Loading demo case: [bold cyan]{demo["title"]}[/bold cyan]', 'white')
        status('Using pre-seeded demo case...')

        case_id = save_case(dispute, demo)

        evidence_list = demo.get('pre_generated_evidence', [])
        witnesses = demo.get('pre_generated_witnesses', [])
        verdict_data = demo.get('pre_generated_verdict', {})
        args = {'prosecution': 'The evidence speaks for itself.', 'defence': 'Reasonable doubt remains.'}
        cross_exams = []

        save_evidence(case_id, evidence_list)
        save_witnesses(case_id, witnesses)

        all_facts = extract_prolog_facts(evidence_list, witnesses)

        status('Running Prolog verdict engine...')
        log('[bold yellow]>>> PROLOG ENGINE ACTIVATED <<<[/bold yellow]')

        try:
            prolog_result = run_verdict(all_facts, _get_defendant_atom(demo.get('defendant', 'defendant')))
        except Exception as e:
            log(f'Prolog fallback: {e}', 'red')
            prolog_result = {
                'verdict': verdict_data.get('verdict', 'undecided'),
                'contradictions': verdict_data.get('contradictions', []),
            }

        _stream_demo_transcript(demo, log)

        status('Archiving to Firebase...')
        trial_data = {
            'title': demo['title'],
            'verdict': prolog_result['verdict'],
            'contradictions': prolog_result['contradictions'],
            'transcript': json.dumps(cross_exams),
        }
        firebase_id = archive_trial(case_id, trial_data) or ''
        save_verdict(case_id, {**prolog_result, 'firebase_id': firebase_id})

        log(f'\n[bold red]━━━ VERDICT: {prolog_result["verdict"].upper()} ━━━[/bold red]')

        return {
            **trial_data,
            'firebase_id': firebase_id,
            'evidence_list': evidence_list,
            'witnesses': witnesses,
        }

    status('Generating case metadata...')
    log('[cyan]STEP 1: Case generation[/cyan]')
    case_data = generate_json('case_gen', dispute=dispute)
    log(f'Case: [bold]{case_data.get("title", "")}[/bold]')
    case_id = save_case(dispute, case_data)

    status('Extracting evidence...')
    log('\n[cyan]STEP 2: Evidence extraction[/cyan]')
    evidence_data = generate_json('evidence_extract', trial_summary=json.dumps(case_data))
    evidence_list = evidence_data.get('evidence_list', [])
    save_evidence(case_id, evidence_list)
    for e in evidence_list:
        log(f'  [yellow]■[/yellow] {e.get("description", "")}')

    status('Generating witnesses...')
    log('\n[cyan]STEP 3: Witness generation[/cyan]')
    witnesses = generate_json(
        'witness_gen',
        case_title=case_data.get('title', ''),
        setting=case_data.get('setting', ''),
        num_witnesses=3,
    )
    if isinstance(witnesses, dict):
        witnesses = witnesses.get('witnesses', [witnesses])
    save_witnesses(case_id, witnesses)
    for w in witnesses:
        log(f'  [magenta]■[/magenta] {w.get("name", "")} — {w.get("occupation", "")}')

    status('Generating lawyer arguments...')
    log('\n[cyan]STEP 4: Lawyer arguments[/cyan]')
    evidence_summary = '; '.join(e.get('description', '') for e in evidence_list)
    args = generate_json(
        'lawyer_args',
        case_title=case_data.get('title', ''),
        evidence_summary=evidence_summary,
    )
    log(f'\n[bold red]PROSECUTION:[/bold red] {args.get("prosecution", "")}')
    log(f'\n[bold blue]DEFENCE:[/bold blue] {args.get("defence", "")}')

    status('Cross-examining witnesses...')
    log('\n[cyan]STEP 5: Cross-examination[/cyan]')
    cross_exams = []
    for witness in witnesses:
        log(f'\n[bold]Witness: {witness.get("name", "")}[/bold]')
        cx = generate_json(
            'cross_exam',
            witness_name=witness.get('name', ''),
            personality=witness.get('personality', ''),
            case_title=case_data.get('title', ''),
            alibi_claim=witness.get('alibi_claim', ''),
            secret=witness.get('secret', ''),
        )
        if isinstance(cx, list):
            for qa in cx:
                log(f'  [bold cyan]{qa.get("questioner", "Q")}:[/bold cyan] {qa.get("question", "")}')
                marker = '[bold red]⚠ CONTRADICTION[/bold red] ' if qa.get('contradiction') else ''
                log(f'  {marker}[italic]{qa.get("answer", "")}[/italic]')
        cross_exams.append(cx)

    status('Running Prolog verdict engine...')
    log('\n[bold yellow]>>> PROLOG ENGINE ACTIVATED <<<[/bold yellow]')
    all_facts = extract_prolog_facts(evidence_list, witnesses)

    defendant_atom = _get_defendant_atom(case_data.get('defendant', 'defendant'))

    try:
        prolog_result = run_verdict(all_facts, defendant_atom)
    except Exception as e:
        log(f'Prolog warning: {e}', 'red')
        prolog_result = {'verdict': 'undecided', 'contradictions': []}

    for contradiction in prolog_result.get('contradictions', []):
        log(f'  [bold red]CONTRADICTION DETECTED:[/bold red] {contradiction}')

    status('Archiving to Firebase...')
    trial_data = {
        'title': case_data.get('title', ''),
        'verdict': prolog_result['verdict'],
        'contradictions': prolog_result['contradictions'],
        'transcript': json.dumps(cross_exams),
    }
    firebase_id = archive_trial(case_id, trial_data) or ''
    save_verdict(case_id, {**prolog_result, 'firebase_id': firebase_id})

    log(f'\n[bold red]━━━ VERDICT: {prolog_result["verdict"].upper()} ━━━[/bold red]')

    return {
        **trial_data,
        'firebase_id': firebase_id,
        'evidence_list': evidence_list,
        'witnesses': witnesses,
    }


def _get_defendant_atom(name: str) -> str:
    return name.lower().replace(' ', '_').replace('-', '_')


def _stream_demo_transcript(demo: dict, log) -> None:
    log(f'\n[bold cyan]━━━ {demo["title"].upper()} ━━━[/bold cyan]')
    log(f'[white]Setting: {demo.get("setting", "")}[/white]')
    log(f'[yellow]Plaintiff: {demo.get("plaintiff", "")}[/yellow]')
    log(f'[red]Defendant: {demo.get("defendant", "")}[/red]')

    log('\n[bold]EVIDENCE BOARD:[/bold]')
    for e in demo.get('pre_generated_evidence', []):
        log(f'  [yellow]■[/yellow] [{e.get("evidence_type", "?")}] {e.get("description", "")}')

    log('\n[bold]WITNESSES:[/bold]')
    for w in demo.get('pre_generated_witnesses', []):
        log(f'  [magenta]■[/magenta] {w.get("name", "")} — {w.get("occupation", "")}')
        log(f'    Alibi: {w.get("alibi_claim", "")}')

    log('\n[bold red]PROSECUTION:[/bold red] The evidence is clear. The defendant had motive, opportunity, and means.')
    log('[bold blue]DEFENCE:[/bold blue] Correlation is not causation. Reasonable doubt persists.')

    log('\n[bold]CROSS-EXAMINATION:[/bold]')
    for witness in demo.get('pre_generated_witnesses', []):
        log(f'\n  [bold]Witness: {witness.get("name", "")}[/bold]')
        log(f'  [bold cyan]PROSECUTION:[/bold cyan] Where were you at the time of the incident?')
        log(f'  [italic]{witness.get("alibi_claim", "")}[/italic]')
        log(f'  [bold cyan]PROSECUTION:[/bold cyan] But our records contradict that claim entirely.')
        log(f'  [bold red]⚠ WITNESS FALTERS[/bold red]')


if __name__ == '__main__':
    init_db()
    VerdictOSApp().run()
