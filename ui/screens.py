import asyncio
import json
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Input, Button, RichLog, Label, DataTable, Footer
from textual.containers import Horizontal, Vertical
from ui.widgets import EvidenceBoard


class CaseInputScreen(Screen):
    CSS = """
    CaseInputScreen {
        align: center middle;
    }
    #wrapper {
        width: 84;
        height: auto;
        border: double #E94560;
        padding: 2 4;
    }
    #title {
        color: #E94560;
        text-style: bold;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }
    #subtitle {
        color: #00D4FF;
        text-align: center;
        width: 100%;
        margin-bottom: 2;
    }
    #dispute_input {
        width: 100%;
        margin-bottom: 1;
    }
    #btn_row {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id='wrapper'):
            yield Label('■ VERDICTOS — AI COURTROOM OPERATING SYSTEM ■', id='title')
            yield Label('GENERATE · INVESTIGATE · ARGUE · DECIDE', id='subtitle')
            yield Input(placeholder='Describe your dispute here...', id='dispute_input')
            with Horizontal(id='btn_row'):
                yield Button('FILE CASE', id='file_btn', variant='error')
                yield Button('DEMO: BIRYANI THEFT', id='demo_biryani', variant='warning')
                yield Button('DEMO: SPIDERMAN', id='demo_spider', variant='warning')
                yield Button('DEMO: ATTENDANCE FRAUD', id='demo_attendance', variant='warning')
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case 'file_btn':
                dispute = self.query_one('#dispute_input', Input).value.strip()
                if dispute:
                    self.app.push_screen(TrialScreen(dispute=dispute, demo_key=None))
            case 'demo_biryani':
                self.app.push_screen(TrialScreen(dispute='', demo_key='biryani'))
            case 'demo_spider':
                self.app.push_screen(TrialScreen(dispute='', demo_key='spiderman'))
            case 'demo_attendance':
                self.app.push_screen(TrialScreen(dispute='', demo_key='attendance'))


class TrialScreen(Screen):
    CSS = """
    TrialScreen {
        layout: vertical;
    }
    #screen_title {
        color: #E94560;
        text-style: bold;
        text-align: center;
        width: 100%;
        padding: 0 1;
        background: #1a0a0a;
    }
    #main_panels {
        height: 1fr;
    }
    #left_panel {
        width: 38%;
        border: solid #E94560;
        padding: 1;
    }
    #right_panel {
        width: 62%;
        border: solid #00D4FF;
        padding: 1;
    }
    .panel-title {
        color: #F5A623;
        text-style: bold;
        margin-bottom: 1;
    }
    #status_bar {
        color: #39FF14;
        text-align: center;
        padding: 0 1;
        background: #001a00;
    }
    """

    def __init__(self, dispute: str, demo_key: str | None, **kwargs):
        super().__init__(**kwargs)
        self.dispute = dispute
        self.demo_key = demo_key

    def compose(self) -> ComposeResult:
        yield Label('■ TRIAL IN PROGRESS ■', id='screen_title')
        with Horizontal(id='main_panels'):
            with Vertical(id='left_panel'):
                yield Label('EVIDENCE BOARD', classes='panel-title')
                yield EvidenceBoard(id='evidence_table')
                yield Label('WITNESSES', classes='panel-title')
                yield DataTable(id='witness_table')
            with Vertical(id='right_panel'):
                yield Label('TRIAL TRANSCRIPT', classes='panel-title')
                yield RichLog(id='transcript', highlight=True, markup=True)
        yield Label('Initialising trial...', id='status_bar')
        yield Footer()

    def on_mount(self) -> None:
        self.query_one('#evidence_table', EvidenceBoard).add_columns('Type', 'Description')
        self.query_one('#witness_table', DataTable).add_columns('Name', 'Alibi')
        self.run_worker(self._run_trial(), exclusive=True)

    def _log(self, msg: str) -> None:
        self.query_one('#transcript', RichLog).write(msg)

    def _status(self, msg: str) -> None:
        self.query_one('#status_bar', Label).update(msg)

    async def _run_trial(self) -> None:
        import services.trial_runner as runner
        from database.db import save_case, save_witnesses, save_evidence

        try:
            if self.demo_key:
                await self._run_demo(runner)
                return

            self._status('[yellow]Generating trial...[/yellow]')

            result = await asyncio.to_thread(
                runner.run_custom_trial,
                self.dispute
            )

            case_data = result["case"]
            evidence_list = result["evidence"]
            witnesses = result["witnesses"]
            lawyers = result["lawyers"]

            self._log(f'[bold white]CASE:[/bold white] {case_data["title"]}')
            self._log(f'[yellow]Setting:[/yellow] {case_data["setting"]}')
            self._log(f'[red]Defendant:[/red] {case_data["defendant"]}')
            self._log(f'[green]Plaintiff:[/green] {case_data["plaintiff"]}')

            ev_table = self.query_one('#evidence_table', EvidenceBoard)

            for e in evidence_list:
                ev_table.add_row(
                    e.get("evidence_type", ""),
                    e.get("description", "")
                )

            wit_table = self.query_one('#witness_table', DataTable)

            for w in witnesses:
                wit_table.add_row(
                    w.get("name", ""),
                    w.get("alibi_claim", "")
                )

            self._log(
                f'[bold red]PROSECUTION:[/bold red] '
                f'{lawyers["prosecution"]}'
            )

            self._log(
                f'[bold blue]DEFENCE:[/bold blue] '
                f'{lawyers["defence"]}'
            )

            verdict = result["verdict"].upper().replace("_", " ")

            self._log(
                f'\n[bold red]━━━ VERDICT: {verdict} ━━━[/bold red]'
            )

            self._status(
                f'[green]Complete. Verdict: {verdict}[/green]'
            )

            await asyncio.sleep(1.5)

            self.app.push_screen(
                VerdictScreen(result=result)
            )


        except Exception as exc:
            self._log(f'[bold red]ERROR: {exc}[/bold red]')
            self._status(f'[red]Error: {exc}[/red]')

    async def _run_demo(self, runner) -> None:
        demo = runner.load_demo(self.demo_key)

        self._status('[yellow]Loading demo case...[/yellow]')
        self._log(f'[bold cyan]━━━ {demo["title"].upper()} ━━━[/bold cyan]')
        self._log(f'[yellow]Setting:[/yellow] {demo.get("setting", "")}')
        self._log(f'[red]Defendant:[/red] {demo.get("defendant", "")}')
        self._log(f'[green]Plaintiff:[/green] {demo.get("plaintiff", "")}')
        self._log(f'[dim]{demo.get("summary", "")}[/dim]')

        await asyncio.sleep(0.3)

        evidence_list = demo.get('pre_generated_evidence', [])
        witnesses = demo.get('pre_generated_witnesses', [])
        ev_table = self.query_one('#evidence_table', EvidenceBoard)
        wit_table = self.query_one('#witness_table', DataTable)

        self._log('\n[bold cyan]━━━ EVIDENCE BOARD ━━━[/bold cyan]')
        for e in evidence_list:
            self._log(f'  [yellow]■[/yellow] [{e.get("evidence_type", "?")}] {e.get("description", "")}')
            ev_table.add_row(e.get('evidence_type', '?'), e.get('description', ''))
            await asyncio.sleep(0.15)

        self._log('\n[bold cyan]━━━ WITNESSES ━━━[/bold cyan]')
        for w in witnesses:
            self._log(f'  [magenta]■[/magenta] {w.get("name", "")} — {w.get("occupation", "")}')
            self._log(f'    Alibi: [italic]{w.get("alibi_claim", "")}[/italic]')
            wit_table.add_row(w.get('name', ''), w.get('alibi_claim', ''))
            await asyncio.sleep(0.15)

        self._log('\n[bold cyan]━━━ OPENING ARGUMENTS ━━━[/bold cyan]')
        self._log('[bold red]PROSECUTION:[/bold red] The evidence is irrefutable. Motive, opportunity, and physical proof place the defendant at the scene.')
        await asyncio.sleep(0.5)
        self._log('[bold blue]DEFENCE:[/bold blue] The prosecution relies on circumstantial evidence. Reasonable doubt has not been eliminated.')
        await asyncio.sleep(0.5)

        self._log('\n[bold cyan]━━━ CROSS-EXAMINATION ━━━[/bold cyan]')
        for witness in witnesses:
            self._log(f'\n[bold white]Witness: {witness.get("name", "")}[/bold white]')
            self._log(f'  [bold red]PROSECUTION:[/bold red] Where exactly were you at the time of the incident?')
            await asyncio.sleep(0.4)
            self._log(f'  [italic]{witness.get("alibi_claim", "")}[/italic]')
            await asyncio.sleep(0.4)
            self._log(f'  [bold red]PROSECUTION:[/bold red] Our records directly contradict that statement.')
            await asyncio.sleep(0.4)
            self._log(f'  [bold red]⚠ WITNESS FALTERS UNDER QUESTIONING[/bold red]')
            await asyncio.sleep(0.3)

        self._status('[yellow]Running Prolog verdict engine...[/yellow]')
        self._log('\n[bold yellow]━━━ PROLOG VERDICT ENGINE ━━━[/bold yellow]')
        await asyncio.sleep(0.3)
        prolog_result = await asyncio.to_thread(
            runner.step_run_prolog, evidence_list, witnesses, demo.get('defendant', 'defendant')
        )
        for c in prolog_result.get('contradictions', []):
            self._log(f'  [bold red]CONTRADICTION DETECTED:[/bold red] {c}')
        if prolog_result.get('error'):
            pre_verdict = demo.get('pre_generated_verdict', {})
            prolog_result = {
                'verdict': pre_verdict.get('verdict', 'guilty'),
                'contradictions': pre_verdict.get('contradictions', []),
            }
            for c in prolog_result['contradictions']:
                self._log(f'  [bold red]CONTRADICTION DETECTED:[/bold red] {c}')

        from database.db import save_case, save_witnesses, save_evidence
        case_id = await asyncio.to_thread(save_case, demo['dispute_text'], demo)
        await asyncio.to_thread(save_evidence, case_id, evidence_list)
        await asyncio.to_thread(save_witnesses, case_id, witnesses)
        firebase_id = await asyncio.to_thread(
            runner.step_archive, case_id, demo['title'], prolog_result, []
        )

        verdict = prolog_result['verdict'].upper().replace('_', ' ')
        self._log(f'\n[bold red]━━━ VERDICT: {verdict} ━━━[/bold red]')
        self._status(f'[green]Complete. Verdict: {verdict}[/green]')
        await asyncio.sleep(1.5)
        self.app.push_screen(VerdictScreen(result={
            'title': demo['title'],
            'verdict': prolog_result['verdict'],
            'contradictions': prolog_result['contradictions'],
            'firebase_id': firebase_id,
            'evidence_list': evidence_list,
            'witnesses': witnesses,
        }))


class VerdictScreen(Screen):
    CSS = """
    VerdictScreen {
        align: center middle;
        background: #0D0D0D;
    }
    #verdict_wrapper {
        width: 84;
        max-height: 40;
        border: double #E94560;
        padding: 2 4;
    }
    #verdict_title {
        color: #E94560;
        text-style: bold;
        text-align: center;
        width: 100%;
        margin-bottom: 2;
    }
    #case_name {
        color: #00D4FF;
        text-style: bold;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }
    #verdict_text {
        text-style: bold;
        text-align: center;
        width: 100%;
        margin-bottom: 2;
    }
    #contradiction_title {
        color: #F5A623;
        text-style: bold;
        width: 100%;
        margin-bottom: 1;
    }
    #contradiction_text {
        color: #FFFFFF;
        width: 100%;
        margin-bottom: 2;
    }
    #firebase_label {
        color: #555555;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }
    #btn_row {
        width: 100%;
        align: center middle;
        margin-top: 1;
    }
    """

    def __init__(self, result: dict, **kwargs):
        super().__init__(**kwargs)
        self.result = result

    def compose(self) -> ComposeResult:
        verdict_raw = self.result.get('verdict', 'undecided')
        verdict_display = verdict_raw.upper().replace('_', ' ')
        title = self.result.get('title', 'Unknown Case')
        contradictions = self.result.get('contradictions', [])
        firebase_id = self.result.get('firebase_id', '')

        verdict_color = '#FF4444' if verdict_raw == 'guilty' else '#39FF14'

        with Vertical(id='verdict_wrapper'):
            yield Label('■ THE COURT HAS REACHED A VERDICT ■', id='verdict_title')
            yield Label(f'CASE: {title}', id='case_name')
            yield Label(f'[{verdict_color}]VERDICT: {verdict_display}[/{verdict_color}]', id='verdict_text', markup=True)

            if contradictions:
                yield Label('CONTRADICTIONS DETECTED BY PROLOG ENGINE:', id='contradiction_title')
                lines = '\n'.join(f'  • {c}' for c in contradictions)
                yield Label(lines, id='contradiction_text')

            if firebase_id:
                yield Label(f'Archived to Firebase: {firebase_id}', id='firebase_label')

            with Horizontal(id='btn_row'):
                yield Button('NEW CASE', id='new_case_btn', variant='error')
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'new_case_btn':
            self.app.pop_screen()
            self.app.pop_screen()
