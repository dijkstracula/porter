import logging
import os
from pathlib import Path

from ivy import ivy_art as iart
from ivy import ivy_actions as iact
from ivy import ivy_compiler as ic
from ivy import ivy_isolate as iiso
from ivy import logic as ilog
from ivy import ivy_module as imod

from . import ast
from .ast import Binding, sorts, terms


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
        print(im.sort_destructors)
        import pdb;
        pdb.set_trace()


def binding_from_ivy_const(c: ilog.Const) -> Binding[sorts.Sort]:
    name = c.name
    sort = sorts.from_ivy(c.sort)
    return Binding(name, sort)


def strip_prefixes(prefixes: list[str], sep: str, s: str) -> str:
    prefix = sep.join(prefixes) + sep
    if s.startswith(prefix):
        return s[len(prefix):]
    return s


# Expression conversion

def expr_from_apply(im: imod.Module, app: ilog.Apply) -> terms.Expr:
    if app.func.name == "+":
        lhs = expr_from_ivy(im, app.args[0])
        rhs = expr_from_ivy(im, app.args[1])
        return terms.BinOp(app, lhs, "+", rhs)
    pass


def expr_from_const(im: imod.Module, c: ilog.Const) -> terms.Constant:
    return terms.Constant(c, c.name)


def expr_from_or(im: imod.Module, expr: ilog.Or) -> terms.Expr:
    if len(expr.terms) == 0:
        return terms.Constant(expr, "false")
    else:
        lhs = expr_from_ivy(im, expr.terms[0])
        for r in expr.terms[1:]:
            rhs = expr_from_ivy(im, r)
            lhs = terms.BinOp(r, lhs, "or", rhs)
        return lhs


def expr_from_and(im: imod.Module, expr: ilog.And) -> terms.Expr:
    if len(expr.terms) == 0:
        return terms.Constant(expr, "true")
    else:
        lhs = expr_from_ivy(im, expr.terms[0])
        for r in expr.terms[1:]:
            rhs = expr_from_ivy(im, r)
            lhs = terms.BinOp(r, lhs, "and", rhs)
        return lhs


def expr_from_ivy(im: imod.Module, expr) -> terms.Expr:
    if isinstance(expr, ilog.Const):
        return expr_from_const(im, expr)
    if isinstance(expr, ilog.Apply):
        return expr_from_apply(im, expr)
    if isinstance(expr, ilog.And):
        return expr_from_and(im, expr)
    if isinstance(expr, ilog.Or):
        return expr_from_or(im, expr)


# Action/statement conversion


def action_def_from_ivy(im: imod.Module, iaction: iact.Action) -> terms.ActionDefinition:
    formal_params = []
    for p in iaction.formal_params:
        binding = binding_from_ivy_const(p)
        binding.name = strip_prefixes(["fml"], ":", binding.name)
        formal_params.append(binding)

    formal_returns = []
    for p in iaction.formal_returns:
        binding = binding_from_ivy_const(p)
        binding.name = strip_prefixes(["fml"], ":", binding.name)
        formal_returns.append(binding)

    body = []
    for a in iaction.args:
        pass  # body.append(action_from_ivy(im, a))
    return terms.ActionDefinition(iaction, formal_params, formal_returns, body)


def record_from_ivy(im: imod.Module, name: str) -> terms.Record:
    if name not in im.sort_destructors:
        raise Exception(f"is {name} the name of a class?")

    # TODO: we should accumulate scopes, I think - nested classes may require more than one name
    # to be stripped.  Should name instead be a scoping context, maybe of type [str]?

    fields = []
    for c in im.sort_destructors[name]:
        f = binding_from_ivy_const(c)
        f.name = strip_prefixes([name], ".", f.name)
        assert isinstance(f.decl, sorts.Function)
        f.decl = f.decl.range
        fields.append(f)

    actions = []
    for (action_name, action) in im.actions.items():
        if not action_name.startswith(name):
            continue
        action_name = strip_prefixes([name], ".", action_name)
        action = action_def_from_ivy(im, action)
        actions.append(Binding(action_name, action))

    # TODO: What's a good ivy ast to pass in here?
    return terms.Record(None, fields, actions)
