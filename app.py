from textual.app import App, ComposeResult
from textual.widgets import Static, Button
from textual.containers import Horizontal, Vertical
from textual import log


def create_app(stream, dataset, classname) -> App:
    class ProdigyApp(App):
        CSS_PATH = ["style.css", "subset.css"]
        TITLE = "Prodigy"

        counts = {
            "accept": 0,
            "reject": 0,
            "ignore": 0
        }

        def render_count(self, kind="accept"):
            if kind == "total":
                n = sum(self.counts.values())
            else:
                n = self.counts[kind]
            msg = f"{kind.upper()}"
            msg += (17 - len(msg)) * " "
            msg += str(n)
            return msg

        def on_button_pressed(self, event: Button.Pressed) -> None:
            """Event handler called when a button is pressed."""
            log(f"button {event.button.id} got clicked")
            log(self.counts)
            if event.button.id == "accept":
                self.counts['accept'] += 1
                self.query_one("#n_accept").update(self.render_count("accept"))
            if event.button.id == "reject":
                self.counts['reject'] += 1
                self.query_one("#n_reject").update(self.render_count("reject"))
            if event.button.id == "ignore":
                self.counts['ignore'] += 1
                self.query_one("#n_ignore").update(self.render_count("ignore"))
            self.query_one("#n_total").update(self.render_count("total"))
            self.query_one("#textcard").update(next(stream)['text'])


        def compose(self) -> ComposeResult:
            """Called to add widgets to the app."""
            yield Vertical(
                Static("Prodigy-TUI", classes="bold text-white text-center"),
                Static("", classes="bold text-gray-100"),
                Static(f"Dataset: {dataset}", classes="text-gray-100"),
                Static("", classes="bold text-gray-100"),
                Static(self.render_count("accept"), classes="bold text-gray-100", id="n_accept"),
                Static(self.render_count("reject"), classes="bold text-gray-100", id="n_reject"),
                Static(self.render_count("ignore"), classes="bold text-gray-100", id="n_ignore"),
                Static("", classes="bold text-gray-100"),
                Static(self.render_count("total"), classes="bold text-gray-100", id="n_total"),
                classes="dock-left h-full bg-gray-500 w-25 p-1 border-r-tall-gray-600"
            )
            yield Vertical(
                Vertical(
                    Static(classname.upper(), classes="bg-purple-600 border-t-tall-purple-100 border-b-tall-purple-900 text-white text-center bold m-1"),
                    Static(next(stream)['text'], classes="bg-white border-b-tall-gray-200 border-b-tall-gray-400 text-black text-center bold w-full h-auto m-1 pt-1", id="textcard"),
                    classes="dock-top"
                ),
                Horizontal(
                    Button("Accept [A]", id="accept", classes="mx-3 w-30p", variant="success",),
                    Button("Reject [X]", id="reject", classes="mx-3 w-30p", variant="error",),
                    Button("Ignore [ ]", id="ignore", classes="mx-3 w-30p", variant="default",),
                    classes="dock-bottom h-4 w-full bg-gray-200"
                )
            )
    return ProdigyApp

stream = ({"text": f"this is example number {i}"} for i in range(1000))
app = create_app(stream=stream, dataset="demo-dataset", classname="POSITIVE SENTIMENT")

if __name__ == "__main__":
    app.run()
