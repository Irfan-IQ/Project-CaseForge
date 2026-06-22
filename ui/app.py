from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from ui.screens import CaseInputScreen


class VerdictOSApp(App):
    CSS_PATH = 'ui/assets/theme.tcss'
    TITLE = 'VERDICT OS · AI COURTROOM OPERATING SYSTEM'
    BINDINGS = [
        ('q', 'quit', 'Quit'),
        ('n', 'new_case', 'New Case'),
    ]

    def on_mount(self) -> None:
        self.push_screen(CaseInputScreen())

    def action_new_case(self) -> None:
        self.pop_screen()
        self.push_screen(CaseInputScreen())
