from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from ui.screens import CaseInputScreen


class VerdictOSApp(App):
    CSS_PATH = 'ui/assets/theme.tcss'
    TITLE = 'VERDICT OS · AI COURTROOM OPERATING SYSTEM'
    BINDINGS = [
        ('q', 'quit', 'Quit'),
    ]

    def on_mount(self) -> None:
        self.push_screen(CaseInputScreen())
