import click
import os
import sys

from pathlib import Path

from .ivy import config, shims

from porter import extraction

sys.setrecursionlimit(1000000)  # booyah
config.init_parameters()


@click.command()
@click.argument('isolate')
def extract(isolate):
    path = Path(isolate)
    if not path.is_absolute():
        path = Path(os.getcwd(), path)

    prog = shims.handle_isolate(path)
    extracted = extraction.extract_java(prog)

    print(extracted)

