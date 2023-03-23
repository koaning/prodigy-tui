from typing import Sequence, Dict
from textual.app import App, ComposeResult
from textual.widgets import Static, Button, TextLog
from textual import events
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual import log
from functools import partial


from prodigy import get_stream

def create_app(stream: Sequence[Dict], dataset:str, label:str) -> App:
    """Creates a Textual app for Prodigy from the Command Line"""
    stream = iter(stream)
    class ProdigyTextcat(App):
        """The Prodigy textcat Widget"""
        CSS_PATH = ["style.css", "subset.css"]
        TITLE = "Prodigy"
        BINDINGS = [
            Binding("a", "on_annot('accept')", "Accept"),
            Binding("x", "on_annot('reject')", "Reject"),
            Binding("space", "on_annot('ignore')", "Ignore")
        ]
        ACTIVE_EFFECT_DURATION = 0.6

        counts = {
            "accept": 0,
            "reject": 0,
            "ignore": 0
        }

        def render_count(self, kind="accept"):
            """Renders a line of text for the sidebar to display counts."""
            if kind == "total":
                n = sum(self.counts.values())
            else:
                n = self.counts[kind]
            msg = f"{kind.upper()}"
            msg += (17 - len(msg)) * " "
            msg += str(n)
            return msg

        def action_on_annot(self, answer:str) -> None:
            self.counts[answer] += 1
            log(self.counts)
            self._handle_annot_effect(answer=answer)
            self.update_view()
        
        def on_button_pressed(self, event: Button.Pressed) -> None:
            """Event handler called when a button is pressed."""
            log(f"button {event.button.id} got clicked")
            self.action_on_annot(answer = event.button.id)
        
        def _handle_annot_effect(self, answer: str) -> None:
            log(f"About to handle effect for {answer=}")
            self.query_one("#textcard").remove_class("border-b-tall-gray-400")
            class_to_add = "border-b-tall-gray-400"
            if answer == "accept":
                class_to_add = "border-b-tall-green-400"
            if answer == "reject":
                class_to_add = "border-b-tall-red-400"
            self.query_one("#textcard").add_class(class_to_add)
            self.set_timer(
                self.ACTIVE_EFFECT_DURATION, lambda: self.query_one("#textcard").remove_class(class_to_add)
            )
            self.set_timer(
                self.ACTIVE_EFFECT_DURATION, lambda: self.query_one("#textcard").add_class("border-b-tall-gray-400")
            )

        def update_view(self):
            self.query_one("#n_accept").update(self.render_count("accept"))
            self.query_one("#n_reject").update(self.render_count("reject"))
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
                    Static(label.upper(), classes="bg-purple-600 border-t-tall-purple-100 border-b-tall-purple-900 text-white text-center bold m-1"),
                    Static(next(stream)['text'], classes="bg-white border-b-tall-gray-400 text-black text-center bold w-full h-auto m-1 pt-1", id="textcard"),
                    classes="dock-top"
                ),
                Horizontal(
                    Button("Accept [A]", id="accept", classes="mx-3 w-20p", variant="success",),
                    Button("Reject [X]", id="reject", classes="mx-3 w-20p", variant="error",),
                    Button("Ignore [ ]", id="ignore", classes="mx-3 w-20p", variant="default",),
                    Button("Undo [⌫]", id="undo", classes="mx-3 w-20p", variant="default",),
                    classes="dock-bottom h-4 w-full bg-gray-200"
                )
            )
    return ProdigyTextcat

stream = get_stream("go-emotions.jsonl", rehash=True)
print(next(stream))
app = create_app(stream=stream, dataset="demo-dataset", label="POSITIVE SENTIMENT")

if __name__ == "__main__":
    app.run()
