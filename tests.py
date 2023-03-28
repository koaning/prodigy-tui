import contextlib
from typing import Any, Dict, Generator, Generic, TypeVar
from pathlib import Path

import pytest 

from prodigy import get_stream
from prodigy.core import Controller
from prodigy.components.db import connect

from app import AppState


@contextlib.contextmanager
def tmp_dataset() -> Generator[str, None, None]:
    db = connect()
    dataset_name = "xxx"
    if dataset_name in db.datasets:
        db.drop_dataset(dataset_name)
    yield dataset_name
    db.drop_dataset(dataset_name)


@pytest.fixture()
def controller():
    with tmp_dataset() as f:
        source = [{"text": f"example {i}"} for i in range(200)]
        stream = get_stream(source, dedup=True, rehash=True)
        print(next(stream))
        components = {
            "dataset": f,
            "view_id": "classification",
            "stream": stream
        }
        return Controller.from_components("textcat.tui.manual", components)


def test_state_starts_empty(controller):
    state = AppState(ctrl=controller, label="DEMO")
    assert sum(state.counts) == 0
    assert len(state.history) == 0


def test_state_updates_after_accept(controller):
    state = AppState(ctrl=controller, label="DEMO")
    state.update("accept")
    assert sum(state.counts.values()) == 1
    assert len(state.history) == 1


@pytest.mark.parametrize("event", ["accept", "skip", "reject"])
def test_state_updates_after_undo(controller, event):
    state = AppState(ctrl=controller, label="DEMO")
    for _ in range(10):
        state.update(event)
        annot = state.history[0]
        assert annot['label'] == "DEMO"
        assert annot['answer'] == event
        assert "timestamp" in annot
        assert "_session_id" in annot

        state.update("undo")
        assert sum(state.counts.values()) == 0
        assert len(state.history) == 0


@pytest.mark.parametrize("event", ["accept", "skip", "reject"])
def test_state_updates_after_undo(controller, event):
    state = AppState(ctrl=controller, label="DEMO")
    for _ in range(100):
        state.update(event)
    state.update("save")
    db = connect()
    examples = db.get_dataset_examples(state.ctrl.dataset)
    assert len(examples) == 100


@pytest.mark.parametrize("event", ["accept", "skip", "reject"])
def test_empty_card(controller, event):
    state = AppState(ctrl=controller, label="DEMO")
    for _ in range(200):
        state.update(event)
    state.update("save")
    assert state.card_contents['text'] == "empty stream"
