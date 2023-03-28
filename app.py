from queue import SimpleQueue, Queue

import datetime as dt 
from radicli import Radicli, Arg
from pathlib import Path 
from typing import Dict, Optional, List
from collections import Counter

from prodigy import get_stream
from prodigy.core import Controller
from prodigy.components.db import connect

from textual.app import App, ComposeResult
from textual.widgets import Static, Button
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual import log

# TODO: 
# - handle edge case when stream is empty


class State:
    def __init__(self, ctrl, label):
        self._ctrl = ctrl
        self.dataset = ctrl.dataset
        self._label = label
        self._queue = ctrl.get_questions(session_id=None)
        self._history = []
        self._lt_counts = Counter({
            "accept": 0,
            "reject": 0,
            "ignore": 0
        })

    @property
    def card_contents(self):
        """For now we only consider text, but we might extend this to other types."""
        if len(self._queue) == 0:
            return {"text": "empty stream. \n\n (this probably means that you've annotated everything.)"}
        return {"text": self._queue[0]['text']}

    @property
    def counts(self):
        """Short term counts can be undone with 'undo'. Long term counts are in db."""
        return Counter([r['answer'] for r in self._history]) + self._lt_counts

    @property
    def history(self):
        return self._history

    def get_dataset_examples(self):
        db = connect()
        return db.get_dataset_examples(self.dataset)

    def _fetch_new_questions(self):
        new_questions = self._ctrl.get_questions(session_id=None)
        hashes = [e['_task_hash'] for e in self._history]
        self._queue = [q for q in new_questions if q['_task_hash'] not in hashes]
    
    def update(self, answer):
        if answer in ['accept', 'reject', 'ignore']:
            self._annot(answer)
        if answer == 'undo':
            self._undo()
        if answer == 'save':
            self._save()
    
    def _annot(self, answer):
        if len(self._queue) == 0:
            return 
        item = self._queue[0].copy()
        self._queue = self._queue[1:]
        item['answer'] = answer
        item['label'] = self._label
        timestamp = dt.datetime.timestamp((dt.datetime.now()))
        item['timestamp'] = timestamp
        self._history.append(item)
        
        if len(self._queue) == 0:
            self._fetch_new_questions()
        
        if len(self._history) > 4:
            item = self._history.pop(0)
            self._ctrl.receive_answers([item])
            self._fetch_new_questions()
    
    def _undo(self):
        if len(self._history) == 0:
            return
        item = self._history.pop(-1)
        self._queue = [item] + self._queue
    
    def _save(self):
        self._ctrl.receive_answers(self._history)
        self._history = []
        self._fetch_new_questions()


def create_app(dataset:str, label:str, ctrl: Controller) -> App:
    """Creates a Textual app for Prodigy from the Command Line"""

    class ProdigyTextcat(App):
        """The Prodigy textcat Widget"""
        CSS_PATH = ["style.css"]
        TITLE = "Prodigy"
        BINDINGS = [
            Binding("a", "on_annot('accept')", "Accept"),
            Binding("x", "on_annot('reject')", "Reject"),
            Binding("space", "on_annot('ignore')", "Ignore"),
            Binding("backspace", "on_annot('undo')", "Undo")
        ]
        ACTIVE_EFFECT_DURATION = 0.6
        state = AppState(ctrl=ctrl, label=label)

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
)
def textcat_tui_manual(dataset:str, source: Path, label: str):
    """Interface for binary text classification from the terminal!"""
    # TODO: why does this give a resource warning?
    stream = get_stream(source, dedup=True, rehash=True)
    components = {
        "dataset": dataset,
        "view_id": "classification",
        "stream": stream
    }
    ctrl = Controller.from_components("textcat.tui.manual", components)
    app = create_app(dataset=dataset, label=label, ctrl=ctrl)
    app().run()

# source = "go-emotions-small.jsonl"
# dataset = "tui-total-demo"
# session_id = None
# stream = get_stream(source, dedup=True, rehash=True)
# components = {
#     "dataset": dataset,
#     "view_id": "classification",
#     "stream": stream
# }
# ctrl = Controller.from_components("textcat.tui.manual", components)
# app = create_app(dataset="demo", label="pos", ctrl=ctrl)

if __name__ == "__main__":
    cli.run()
    # app.run()
