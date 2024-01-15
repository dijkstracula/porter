import os

from ivy import ivy_actions as iact
from ivy import ivy_compiler as ic
from ivy import ivy_module as imod
from ivy import ivy_isolate as iiso

import io
from typing import Tuple


def isolate_boilerplate(contents: str) -> str:
    return "\n".join(["#lang ivy1.8",
                      "include numbers",
                      f"{contents}"])


def extract_after_init(im: imod.Module) -> iact.Action:
    action_body = im.initial_actions[0]
    assert isinstance(action_body, iact.LocalAction)
    action_stmts = action_body.args[1]  # "let test_expr := ... in { let ensure... in ... }"
    assert isinstance(action_stmts, iact.Action)
    return action_stmts


def compile_toplevel(tl: str) -> Tuple[imod.Module, ic.AnalysisGraph]:
    return compile_ivy(isolate_boilerplate(tl))


def compile_ivy(file) -> Tuple[imod.Module, ic.AnalysisGraph]:
    with imod.Module() as im:
        if isinstance(file, str):
            file = io.StringIO(file)
        ic.ivy_load_file(file, create_isolate=False)
        iiso.create_isolate('this')
        return im, ic.ivy_new()
