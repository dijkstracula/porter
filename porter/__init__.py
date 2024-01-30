import click

from pathlib import Path

from .ivy import config, shims

config.init_parameters()


@click.command()
@click.argument('isolate')
def generate(isolate):
    shims.handle_isolate(Path(isolate))
