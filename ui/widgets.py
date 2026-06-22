from textual.widgets import DataTable


class EvidenceBoard(DataTable):
    DEFAULT_CSS = """
    EvidenceBoard {
        border: solid #E94560;
        height: auto;
        max-height: 20;
    }
    """
