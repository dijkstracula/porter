import logging
import os

from pathlib import Path

from ivy import ivy_art as iart
from ivy import ivy_compiler as ic
from ivy import ivy_isolate as iiso
from ivy import ivy_logic as il
from ivy import ivy_module as imod

def compile_progtext(path: Path) -> iart.AnalysisGraph:
    logging.info(f"Compiling {path}")
    cwd = os.getcwd()
    os.chdir(path.parent)
    with open(path) as f:
        ic.ivy_load_file(f, create_isolate=False)
        iiso.create_isolate('this')
    os.chdir(cwd)
    return ic.ivy_new()

def handle_isolate(path: Path):
    with imod.Module() as im:
        ag = compile_progtext(path)
        import pdb; pdb.set_trace()
        return ag
