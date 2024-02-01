import ast
import os

from ivy import ivy_actions as iact
from ivy import ivy_compiler as ic
from ivy import ivy_module as imod
from ivy import ivy_isolate as iiso

import io
from typing import Any, Tuple

progdir = os.path.join(os.path.dirname(__file__), 'programs')


def isolate_boilerplate(contents: str) -> str:
    return "\n".join(["#lang ivy1.8",
                      "include numbers",
                      f"{contents}"])


def compile_annotated_expr(sort: str, expr: str) -> Tuple[imod.Module, Any]:
    init_act = "after init { " \
               f"""var test_expr: {sort} := {expr};
                var ensure_no_dead_code_elim: {sort} := test_expr;
                test_expr := ensure_no_dead_code_elim;
            }}"""
    (im, _) = compile_toplevel(init_act)

    test_expr_assign = extract_after_init(im).args[0]
    assert isinstance(test_expr_assign, iact.AssignAction)
    assign_rhs = test_expr_assign.args[1]
    return im, assign_rhs


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
