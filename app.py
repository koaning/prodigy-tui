import datetime as dt 
from radicli import Radicli, Arg
from pathlib import Path 
from typing import Dict, Optional, List
from collections import Counter

from prodigy import get_stream
from prodigy.core import Controller

from textual.app import App, ComposeResult
from textual.widgets import Static, Button
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual import log

# TODO: 
# - handle edge case when stream is empty

class AppState:
    def __init__(self, ctrl: Controller, session_id=None, label=None) -> None:
        self.ctrl = ctrl
        self.session_id = session_id
        self.batch_now: List[Dict] = self.ctrl.get_questions(session_id=session_id)
        self.history: List[Dict] = []
        self.idx: int = 0
        self.label = label
        self._lt_counts = Counter({
            "accept": 0,
            "reject": 0,
            "ignore": 0
        })
    
    @property
    def card_contents(self):
        """For now we only consider text, but we might extend this to other types."""
        if len(self.batch_now) == 0:
            return {"text": "empty stream"}
        return {"text": self.batch_now[self.idx]['text']}

    @property
    def counts(self):
        """Short term counts can be undone with 'undo'. Long term counts are in db."""
        return Counter([r['answer'] for r in self.history]) + self._lt_counts
    
    def update(self, event: str):
        if event in ["accept", "reject", "ignore"]:
            self._annotate_current(answer=event)
        if event == "save":
            self._save_full_history()
        if event == "undo":
            self._undo_annot()
    
    def _annotate_current(self, answer:str) -> None:
        self._set_answer_current_example(answer=answer)
        self.history.append(self.batch_now[self.idx])
        if self.idx >= (len(self.batch_now) - 1):
            self.history.pop(0)
            result = self.batch_now.pop(0)
            self._lt_counts[result['answer']] += 1
            self.ctrl.receive_answers([result], session_id=self.session_id)
            self.batch_now = self.ctrl.get_questions(session_id=self.session_id)
            self.idx = len(self.batch_now) - 1
        else:
            self.idx += 1
        self.counts[answer] += 1
    
    def _undo_annot(self) -> None:
        if self.idx == 0:
            return 
        self.idx -= 1
        self.history.pop(len(self.history) - 1)
    
    def _save_full_history(self) -> None:
        for r in self.history:
            self._lt_counts[r['answer']] += 1
        self.ctrl.receive_answers(self.history)
        self.batch_now = self.ctrl.get_questions(session_id=self.session_id)
        self.idx = 0
        self.history = []

    def _set_answer_current_example(self, answer: str) -> None:
        if answer == "undo":
            return
        self.batch_now[self.idx]["answer"] = answer
        self.batch_now[self.idx]["_session_id"] = self.session_id
        self.batch_now[self.idx]["label"] = self.label
        timestamp = dt.datetime.timestamp((dt.datetime.now()))
        self.batch_now[self.idx]["timestamp"] = int(timestamp)


def create_app(dataset:str, label:str, ctrl: Controller, session_id: Optional[str]=None) -> App:
    """Creates a Textual app for Prodigy from the Command Line"""

    class ProdigyTextcat(App):
        """The Prodigy textcat Widget"""
        CSS_PATH = ["style.css", "subset.css"]
        TITLE = "Prodigy"
        BINDINGS = [
            Binding("a", "on_annot('accept')", "Accept"),
            Binding("x", "on_annot('reject')", "Reject"),
            Binding("space", "on_annot('ignore')", "Ignore"),
            Binding("backspace", "on_annot('undo')", "Undo")
        ]
        ACTIVE_EFFECT_DURATION = 0.6
        state = AppState(ctrl=ctrl, session_id=session_id, label=label)

        def render_count(self, kind="accept"):
            """Renders a line of text for the sidebar to display counts."""
            if kind == "total":
                n = sum(self.state.counts.values())
            else:
                n = self.state.counts[kind]
            msg = f"{kind.upper()}"
            msg += (17 - len(msg)) * " "
            msg += str(n)
            return msg

        def action_on_annot(self, answer:str) -> None:
            self._handle_annot_effect(answer=answer)
            self.state.update(event=answer)
            self.update_view()
        
        def on_button_pressed(self, event: Button.Pressed) -> None:
            self.action_on_annot(answer = event.button.id)
        
        def _handle_annot_effect(self, answer: str) -> None:
            self.query_one("#textcard").remove_class("base-card-border")
            class_to_add = "gray-card-border"
            if answer == "accept":
                class_to_add = "green-card-border"
            if answer == "reject":
                class_to_add = "red-card-border"
            self.query_one("#textcard").add_class(class_to_add)
            self.set_timer(
                self.ACTIVE_EFFECT_DURATION, lambda: self.query_one("#textcard").remove_class(class_to_add)
            )
            self.set_timer(
                self.ACTIVE_EFFECT_DURATION, lambda: self.query_one("#textcard").add_class("base-card-border")
            )

        def _annot_str(self, ex:Dict):
            answer, txt = ex["answer"], ex["text"]
            if len(txt) >= 15:
                txt = txt[:15] + "..."
            if answer == "accept":
                return f"✅ {txt}"
            if answer == "reject":
                return f"❌ {txt}"
            if answer == "ignore":
                return f"⏩ {txt}"
            raise ValueError("answer can only be accept/reject/skip in sidebar")

        def _history_str(self):
            truncated = [self._annot_str(ex) for ex in self.state.history]
            return "\n".join(truncated)

        def update_view(self):
            self.query_one("#n_accept").update(self.render_count("accept"))
            self.query_one("#n_reject").update(self.render_count("reject"))
            self.query_one("#n_ignore").update(self.render_count("ignore"))
            self.query_one("#n_total").update(self.render_count("total"))
            self.query_one("#textcard").update(self.state.card_contents['text'])
            self.query_one("#history").update(self._history_str())

        def compose(self) -> ComposeResult:
            """Called to add widgets to the app."""
            yield Vertical(
                Static("Prodigy-TUI", classes="bold text-center"),
                Static("",),
                Button("💾", id="save", classes="mx-3", variant="primary",),
                Static("",),
                Static(f"Dataset: {dataset}", classes="text-center"),
                Static(f"Session: {session_id}", classes="text-center"),
                Static("",),
                Static("Progress", classes="bold text-center"),
                Static("",),
                Static(self.render_count("accept"), classes="bold", id="n_accept"),
                Static(self.render_count("reject"), classes="bold", id="n_reject"),
                Static(self.render_count("ignore"), classes="bold", id="n_ignore"),
                Static("",),
                Static(self.render_count("total"), classes="bold", id="n_total"),
                Static("History", classes="bold text-center"),
                Static("",),
                Static("", classes="bold", id="history"),
                classes="sidebar"
            )
            yield Vertical(
                Vertical(
                    Static(label.upper(), classes="labelname"),
                    Static(self.state.card_contents['text'], classes="text-card base-card-border text-center bold", id="textcard"),
                    classes="dock-top"
                ),
                Horizontal(
                    Static("", classes="box"),
                    Horizontal(
                        Button("Accept [A]", id="accept", classes="btn", variant="success",),
                        Button("Reject [X]", id="reject", classes="btn", variant="error",),
                        Button("Ignore [ ]", id="ignore", classes="btn", variant="default",),
                        Button("Undo [⌫]", id="undo", classes="btn", variant="default",),
                        classes="btn-container"
                    ),
                    Static("", classes="box"),
                    classes="dock-bottom"
                )
            )
    return ProdigyTextcat

# stream = get_stream("go-emotions-small.jsonl", rehash=True)

cli = Radicli()

@cli.command(
    "textcat.tui.manual",
    dataset=Arg(help="dataset to write annotations into"),
    source=Arg(help="path to text source"),
    label=Arg("--label", "-l", help="category label to apply, only binary is supported"),
    session_id=Arg("--session-id", "-s", help="session_id to attach to annotations")
)
def textcat_tui_manual(dataset:str, source: Path, label: str, session_id: str=None):
    """Interface for binary text classification from the terminal!"""
    # TODO: why does this give a resource warning?
    stream = get_stream(source, dedup=True, rehash=True)
    components = {
        "dataset": dataset,
        "view_id": "classification",
        "stream": stream
    }
    ctrl = Controller.from_components("textcat.tui.manual", components)
    app = create_app(dataset=dataset, label=label, ctrl=ctrl, session_id=session_id)
    app().run()

source = "go-emotions-small.jsonl"
dataset = "tui-total-demo"
session_id = None
stream = get_stream(source, dedup=True, rehash=True)
components = {
    "dataset": dataset,
    "view_id": "classification",
    "stream": stream
}
ctrl = Controller.from_components("textcat.tui.manual", components)
app = create_app(dataset="demo", label="pos", ctrl=ctrl, session_id=session_id)

if __name__ == "__main__":
    cli.run()
    # app.run()
