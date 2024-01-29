import click

from pathlib import Path

from .ivy import shims


@click.command()
@click.argument('isolate')
def generate(isolate):
    shims.handle_isolate(Path(isolate))
