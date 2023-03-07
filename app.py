from textual.app import App, ComposeResult
from textual.widgets import Static, Button
from textual.containers import Horizontal, Vertical


class PaddingDemo(App):
    CSS_PATH = ["style.css", "tuilwind.css"]
    TITLE = "Prodigy"

    def compose(self) -> ComposeResult:
        """Called to add widgets to the app."""
        yield Static("Prodigy-TUI",  classes="dock-left h-full bg-gray-400 text-center bold w-25 p-1")
        yield Vertical(
            Vertical(
                Static("CLASSNAME", classes="bg-purple-600 text-white text-center bold h-1"),
                Static("This is input text.", classes="bg-white text-black text-center bold w-full h-1"),
                classes="dock-top"
            ),
            Horizontal(
                Button("Accept [A]", id="accept", classes="mx-3 w-30p", variant="success"),
                Button("Reject [X]", id="reject", classes="mx-3 w-30p", variant="error"),
                Button("Ignore [ ]", id="ignore", classes="mx-3 w-30p", variant="default"),
                classes="dock-bottom h-4 w-full bg-gray-200"
            )
        )

if __name__ == "__main__":
    app = PaddingDemo()
    app.run()
