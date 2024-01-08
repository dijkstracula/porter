import click

from pathlib import Path

from . import ivy_shim

@click.command()
@click.argument('isolate')
def generate(isolate):
    new = ivy_shim.handle_isolate(Path(isolate))
