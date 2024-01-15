import logging
import os
from pathlib import Path

from ivy import ivy_actions as iact
from ivy import ivy_art as iart
from ivy import ivy_ast as iast
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
    func = expr_from_ivy(im, app.args[0])
    assert isinstance(func, terms.Constant)
    args = [expr_from_ivy(im, a) for a in app.args[1:]]
    return terms.Apply(app, func, args)


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


def expr_from_atom(im: imod.Module, expr: iast.Atom) -> terms.Apply:
    relsym = expr.rep
    args = [expr_from_ivy(im, a) for a in expr.args]
    return terms.Apply(expr, relsym, args)


def expr_from_ivy(im: imod.Module, expr) -> terms.Expr:
    if isinstance(expr, ilog.Apply):
        return expr_from_apply(im, expr)
    if isinstance(expr, iast.Atom):
        return expr_from_atom(im, expr)
    if isinstance(expr, ilog.Const):
        return expr_from_const(im, expr)
    if isinstance(expr, ilog.And):
        return expr_from_and(im, expr)
    if isinstance(expr, ilog.Or):
        return expr_from_or(im, expr)
    raise Exception(f"TODO: {expr}")


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

    body = action_from_ivy(im, iaction)
    return terms.ActionDefinition(iaction, formal_params, formal_returns, body)


def assign_action_from_ivy(im: imod.Module, iaction: iact.AssignAction) -> terms.Assign:
    lhs = expr_from_ivy(im, iaction.args[0])
    rhs = expr_from_ivy(im, iaction.args[1])
    return terms.Assign(iaction, lhs, rhs)


def call_action_from_ivy(im: imod.Module, iaction: iact.CallAction) -> terms.Action:
    assert isinstance(iaction.args[0], iast.Atom)  # Application expression
    call_action = terms.Call(iaction, expr_from_atom(im, iaction.args[0]))
    if len(iaction.args) == 2:
        # TODO: multiple return values probably aren't constants?  Or do we have
        # more args in the iaction?
        assert isinstance(iaction.args[1], ilog.Const)  # return temporary
        temp = binding_from_ivy_const(iaction.args[1])
        return terms.Let(iaction, [temp], call_action)
    else:
        assert len(iaction.args) == 1
        return call_action


def local_action_from_ivy(im: imod.Module, iaction: iact.LocalAction) -> terms.Let:
    assert isinstance(iaction.args[0], ilog.Const)  # Binding name
    varname = binding_from_ivy_const(iaction.args[0])
    assert isinstance(iaction.args[1], iact.Action)
    act = action_from_ivy(im, iaction.args[1])
    return terms.Let(im, [varname], act)


def action_from_ivy(im: imod.Module, act: iact.Action) -> terms.Action:
    if isinstance(act, iact.AssignAction):
        return assign_action_from_ivy(im, act)
    if isinstance(act, iact.LocalAction):
        return local_action_from_ivy(im, act)
    if isinstance(act, iact.CallAction):
        return call_action_from_ivy(im, act)
    if isinstance(act, iact.Sequence):
        subacts = [action_from_ivy(im, a) for a in act.args]
        if len(subacts) == 1:
            return subacts[0]
        return terms.Sequence(act, subacts)
    raise Exception(f"TODO: {type(act)}")


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
