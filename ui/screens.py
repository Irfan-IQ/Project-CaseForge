import asyncio
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Input, Button, RichLog, Label, DataTable, Footer, Static
from textual.containers import Horizontal, Vertical, ScrollableContainer
from ui.widgets import EvidenceBoard


class CaseInputScreen(Screen):
    CSS = """
    CaseInputScreen {
        align: center middle;
    }
    #wrapper {
        width: 80;
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
    }
    #file_btn {
        margin-right: 2;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id='wrapper'):
            yield Label('■ VERDICTOS — AI COURTROOM OPERATING SYSTEM ■', id='title')
            yield Label('GENERATE · INVESTIGATE · ARGUE · DECIDE', id='subtitle')
            yield Input(placeholder='Describe your dispute...', id='dispute_input')
            with Horizontal(id='btn_row'):
                yield Button('FILE CASE', id='file_btn', variant='error')
                yield Button('DEMO: BIRYANI THEFT', id='demo_biryani', variant='warning')
                yield Button('DEMO: SPIDERMAN', id='demo_spider', variant='warning')
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
    }
    #main_panels {
        height: 1fr;
    }
    #left_panel {
        width: 40%;
        border: solid #E94560;
        padding: 1;
    }
    #right_panel {
        width: 60%;
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
                evidence_board = EvidenceBoard(id='evidence_table')
                yield evidence_board
                yield Label('WITNESSES', classes='panel-title')
                yield DataTable(id='witness_table')
            with Vertical(id='right_panel'):
                yield Label('TRIAL TRANSCRIPT', classes='panel-title')
                yield RichLog(id='transcript', highlight=True, markup=True)
        yield Label('Initialising trial pipeline...', id='status_bar')
        yield Footer()

    def on_mount(self) -> None:
        evidence_board = self.query_one('#evidence_table', EvidenceBoard)
        evidence_board.add_columns('Type', 'Description')
        witness_table = self.query_one('#witness_table', DataTable)
        witness_table.add_columns('Name', 'Alibi')
        self.run_worker(self._run_trial(), exclusive=True)

    async def _run_trial(self) -> None:
        from main import run_trial

        transcript = self.query_one('#transcript', RichLog)
        status = self.query_one('#status_bar', Label)

        def log(msg: str, style: str = 'white') -> None:
            transcript.write(f'[{style}]{msg}[/{style}]')

        def set_status(msg: str) -> None:
            status.update(msg)

        try:
            set_status('[yellow]Loading case...[/yellow]')
            result = await asyncio.get_event_loop().run_in_executor(
                None, run_trial, self.dispute, self.demo_key, log, set_status
            )

            ev_table = self.query_one('#evidence_table', EvidenceBoard)
            for e in result.get('evidence_list', []):
                ev_table.add_row(e.get('evidence_type', '?'), e.get('description', ''))

            wit_table = self.query_one('#witness_table', DataTable)
            for w in result.get('witnesses', []):
                wit_table.add_row(w.get('name', ''), w.get('alibi_claim', ''))

            set_status('[green]Trial complete. Pushing verdict...[/green]')
            await asyncio.sleep(1.5)
            self.app.push_screen(VerdictScreen(result=result))

        except Exception as exc:
            log(f'[bold red]ERROR: {exc}[/bold red]')
            set_status(f'[red]Pipeline error: {exc}[/red]')


class VerdictScreen(Screen):
    CSS = """
    VerdictScreen {
        align: center middle;
        background: #0D0D0D;
    }
    #verdict_wrapper {
        width: 80;
        border: double #E94560;
        padding: 2 4;
        align: center middle;
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
        color: #39FF14;
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
        color: #888888;
        text-align: center;
        width: 100%;
    }
    #new_case_btn {
        margin-top: 2;
    }
    """

    def __init__(self, result: dict, **kwargs):
        super().__init__(**kwargs)
        self.result = result

    def compose(self) -> ComposeResult:
        verdict = self.result.get('verdict', 'undecided').upper().replace('_', ' ')
        title = self.result.get('title', 'Unknown Case')
        contradictions = self.result.get('contradictions', [])
        firebase_id = self.result.get('firebase_id', '')

        verdict_color = '#39FF14' if verdict == 'GUILTY' else '#00D4FF'

        with Vertical(id='verdict_wrapper'):
            yield Label('■ THE COURT HAS REACHED A VERDICT ■', id='verdict_title')
            yield Label(f'CASE: {title}', id='case_name')
            yield Label(f'VERDICT: {verdict}', id='verdict_text')

            if contradictions:
                yield Label('CONTRADICTIONS DETECTED:', id='contradiction_title')
                contradiction_lines = '\n'.join(f'  • {c}' for c in contradictions)
                yield Label(contradiction_lines, id='contradiction_text')

            if firebase_id:
                yield Label(f'Archived to Firebase: {firebase_id}', id='firebase_label')

            yield Button('NEW CASE', id='new_case_btn', variant='error')
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'new_case_btn':
            self.app.pop_screen()
            self.app.pop_screen()
