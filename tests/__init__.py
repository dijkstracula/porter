from ivy import ivy_compiler as ic
from ivy import ivy_module as imod
from ivy import ivy_isolate as iiso

import io

from typing import Tuple


def isolate_boilerplate(contents: str) -> str:
    return "\n".join(["#lang ivy1.8",
                      "include numbers",
                      f"{contents}"])


def compile_toplevel(tl: str) -> Tuple[imod.Module, ic.AnalysisGraph]:
    return compile_ivy(isolate_boilerplate(tl))


def compile_ivy(file: str) -> Tuple[imod.Module, ic.AnalysisGraph]:
    with imod.Module() as im:
        ic.ivy_load_file(io.StringIO(file), create_isolate=False)
        iiso.create_isolate('this')
        return im, ic.ivy_new()
