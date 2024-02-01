import click
import sys

from pathlib import Path

from .ivy import config, shims

sys.setrecursionlimit(1000000)  # booyah
config.init_parameters()


@click.command()
@click.argument('isolate')
def generate(isolate):
    shims.handle_isolate(Path(isolate))
