from pathlib import Path

from prodigy import get_stream
from prodigy.core import Controller
from radicli import Arg, Radicli

from .app import create_app

cli = Radicli()


@cli.command(
    "textcat.manual",
    dataset=Arg(help="dataset to write annotations into"),
    source=Arg(help="path to text source"),
    label=Arg(
        "--label", "-l", help="category label to apply, only binary is supported"
    ),
)
def textcat_tui_manual(dataset: str, source: Path, label: str):
    """Interface for binary text classification from the terminal!"""
    # TODO: why does this give a resource warning?
    stream = get_stream(source, dedup=True, rehash=True)
    components = {"dataset": dataset, "view_id": "classification", "stream": stream}
    ctrl = Controller.from_components("textcat.tui.manual", components)
    app = create_app(dataset=dataset, label=label, ctrl=ctrl)
    app().run()


if __name__ == "__main__":
    cli.run()
