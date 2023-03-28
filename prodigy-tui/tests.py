import contextlib
from typing import Generator

import pytest
from app import State
from prodigy import get_stream
from prodigy.components.db import connect
from prodigy.core import Controller


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
        source = [{"text": f"example {i}"} for i in range(20)]
        stream = get_stream(source, dedup=True, rehash=True)
        components = {"dataset": f, "view_id": "classification", "stream": stream}
        return Controller.from_components("textcat.tui.manual", components)


def test_state_starts_empty(controller):
    state = State(ctrl=controller, label="DEMO")
    assert sum(state.counts) == 0
    assert len(state.history) == 0


def test_state_updates_after_accept(controller):
    state = State(ctrl=controller, label="DEMO")
    state.update("accept")
    assert sum(state.counts.values()) == 1
    assert len(state.history) == 1


@pytest.mark.parametrize("event", ["accept", "ignore", "reject"])
def test_state_updates_after_undo(controller, event):
    state = State(ctrl=controller, label="DEMO")
    for _ in range(10):
        state.update(event)
        annot = state.history[0]
        assert annot["label"] == "DEMO"
        assert annot["answer"] == event
        assert "timestamp" in annot

        state.update("undo")
        assert sum(state.counts.values()) == 0
        assert len(state.history) == 0


@pytest.mark.parametrize("event", ["accept", "ignore", "reject"])
def test_state_updates_after_save(controller, event):
    state = State(ctrl=controller, label="DEMO")
    for _ in range(20):
        state.update(event)
    state.update("save")
    db = connect()
    examples = db.get_dataset_examples(state.dataset)
    assert len(examples) == 20


@pytest.mark.parametrize("event", ["accept", "ignore", "reject"])
def test_state_updates_after_many_hits(controller, event):
    state = State(ctrl=controller, label="DEMO")
    # This is way more than we have
    for _ in range(100):
        state.update(event)
    # Still need to hit save to get the stuff in the history.
    state.update("save")
    db = connect()
    examples = db.get_dataset_examples(state.dataset)
    assert len(examples) == 20
    assert sum(state.counts.values()) == 20


@pytest.mark.parametrize("event", ["accept", "ignore", "reject"])
def test_empty_card(controller, event):
    state = State(ctrl=controller, label="DEMO")
    for _ in range(20):
        state.update(event)
    state.update("save")
    assert "empty stream" in state.card_contents["text"]
