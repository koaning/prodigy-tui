from textual.app import App, ComposeResult
from textual.widgets import Static, Button
from textual.containers import Horizontal, Vertical

def create_app(stream, dataset) -> App:
    class ProdigyApp(App):
        CSS_PATH = ["style.css", "tuilwind.css"]
        TITLE = "Prodigy"

        def compose(self) -> ComposeResult:
            """Called to add widgets to the app."""
            yield Vertical(
                Static("Prodigy-TUI", classes="bold text-white text-center"),
                Static("", classes="bold text-gray-100"),
                Static(f"Dataset: {dataset}", classes="text-gray-100"),
                Static("", classes="bold text-gray-100"),
                Static("ACCEPT: 12", classes="bold text-gray-100"),
                Static("REJECT:  1", classes="bold text-gray-100"),
                Static("IGNORE:  0", classes="bold text-gray-100"),
                Static("", classes="bold text-gray-100"),
                Static("TOTAL:  13", classes="bold text-gray-100"),
                classes="dock-left h-full bg-gray-500 w-25 p-1 border-r-tall-gray-600"
            )
            yield Vertical(
                Vertical(
                    Static("CLASSNAME", classes="bg-purple-600 border-t-tall-purple-100 border-b-tall-purple-900 text-white text-center bold m-1"),
                    Static(stream[0]['text'], classes="bg-white border-b-tall-gray-200 border-b-tall-gray-400 text-black text-center bold w-full h-auto m-1 pt-1"),
                    classes="dock-top"
                ),
                Horizontal(
                    Button("Accept [A]", id="accept", classes="mx-3 w-30p", variant="success"),
                    Button("Reject [X]", id="reject", classes="mx-3 w-30p", variant="error"),
                    Button("Ignore [ ]", id="ignore", classes="mx-3 w-30p", variant="default"),
                    classes="dock-bottom h-4 w-full bg-gray-200"
                )
            )
    return ProdigyApp

app = create_app(stream=[{"text": "This is input text.\nThere's lots of it."}], dataset="demo-dataset")

if __name__ == "__main__":
    app.run()
