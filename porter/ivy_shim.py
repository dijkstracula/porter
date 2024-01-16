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
    if app.func.name in ['+', "<=", "<", ">", ">="]:
        lhs = expr_from_ivy(im, app.args[0])
        rhs = expr_from_ivy(im, app.args[1])
        return terms.BinOp(app, lhs, app.func.name, rhs)
    func = expr_from_ivy(im, app.args[0])
    args = [expr_from_ivy(im, a) for a in app.args[1:]]
    return terms.Apply(app, func, args)


def expr_from_const(im: imod.Module, c: ilog.Const) -> terms.Constant:
    return terms.Constant(c, c.name)


def expr_from_var(im: imod.Module, v: ilog.Var) -> terms.Constant:
    return terms.Constant(v, v.name)


def expr_from_or(im: imod.Module, expr: ilog.Or) -> terms.Expr:
    if len(expr.terms) == 0:
        return terms.Constant(expr, "false")
    else:
        lhs = expr_from_ivy(im, expr.terms[0])
        for r in expr.terms[1:]:
            rhs = expr_from_ivy(im, r)
            lhs = terms.BinOp(r, lhs, "or", rhs)
        return lhs


def expr_from_implies(im: imod.Module, expr: ilog.Implies) -> terms.Expr:
    assert len(expr.args) == 2
    lhs = expr_from_ivy(im, expr.args[0])
    rhs = expr_from_ivy(im, expr.args[1])
    return terms.BinOp(expr, lhs, "implies", rhs)


def expr_from_eq(im: imod.Module, expr: ilog.Eq) -> terms.Expr:
    lhs = expr_from_ivy(im, expr.t1)
    rhs = expr_from_ivy(im, expr.t2)
    return terms.BinOp(expr, lhs, "==", rhs)


def expr_from_not(im: imod.Module, expr: ilog.Not) -> terms.Expr:
    lhs = expr_from_ivy(im, expr.args[0])
    return terms.UnOp(expr, "-", lhs)


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
    if isinstance(expr, ilog.Var):
        return expr_from_var(im, expr)
    if isinstance(expr, ilog.And):
        return expr_from_and(im, expr)
    if isinstance(expr, ilog.Or):
        return expr_from_or(im, expr)
    if isinstance(expr, ilog.Implies):
        return expr_from_implies(im, expr)
    if isinstance(expr, ilog.Eq):
        return expr_from_eq(im, expr)
    if isinstance(expr, ilog.Not):
        return expr_from_not(im, expr)
    raise Exception(f"TODO: {expr}")


# Action/statement conversion


def action_kind_from_action_name(name: str) -> terms.ActionKind:
    if name.startswith("ext:"):
        return terms.ActionKind.EXPORTED
    if name.startswith("imp"):
        return terms.ActionKind.IMPORTED
    return terms.ActionKind.NORMAL


def action_def_from_ivy(im: imod.Module, name: str, iaction: iact.Action) -> terms.ActionDefinition:
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
    kind = action_kind_from_action_name(name)

    return terms.ActionDefinition(iaction, kind, formal_params, formal_returns, body)


def assign_action_from_ivy(im: imod.Module, iaction: iact.AssignAction) -> terms.Assign:
    lhs = expr_from_ivy(im, iaction.args[0])
    rhs = expr_from_ivy(im, iaction.args[1])
    return terms.Assign(iaction, lhs, rhs)


def assume_action_from_ivy(im: imod.Module, iaction: iact.AssumeAction) -> terms.Assume:
    pred = expr_from_ivy(im, iaction.args[0])
    return terms.Assume(im, pred)


def call_action_from_ivy(im: imod.Module, iaction: iact.CallAction) -> terms.Action:
    assert isinstance(iaction.args[0], iast.Atom)  # Application expression
    call_action = terms.Call(iaction, expr_from_atom(im, iaction.args[0]))
    if len(iaction.args) == 2:
        # In this case, the call action returns a value.
        lhs = expr_from_ivy(im, iaction.args[1])
        rhs = call_action.app
        return terms.Assign(iaction, lhs, rhs)
    else:
        # In this case, the call action is entirely side-effecting.
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
    if isinstance(act, iact.AssumeAction):
        return assume_action_from_ivy(im, act)
    if isinstance(act, iact.LocalAction):
        return local_action_from_ivy(im, act)
    if isinstance(act, iact.CallAction):
        return call_action_from_ivy(im, act)
    if isinstance(act, iact.Sequence):
        subacts = [action_from_ivy(im, a) for a in act.args]
        if len(subacts) == 1:
            return subacts[0]
        return terms.Sequence(act, subacts)
    if isinstance(act, iact.HavocAction):
        return None # XXX: Hole
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
        action = action_def_from_ivy(im, action_name, action)
        actions.append(Binding(action_name, action))

    # TODO: What's a good ivy ast to pass in here?
    return terms.Record(None, fields, actions)


def program_from_ivy(im: imod.Module) -> terms.Program:
    porter_sorts = [sorts.from_ivy(s) for s in im.sig.sorts.values()]
    individuals = [binding_from_ivy_const(sym) for name, sym in im.sig.symbols.items() if name != "<"]  # XXX: hack
    inits = [action_from_ivy(im, a) for a in im.initial_actions]
    actions = [Binding(name, action_def_from_ivy(im, name, a)) for name, a in im.actions.items()]

    # TODO: What's a good ivy ast to pass in here?
    return terms.Program(None, porter_sorts, individuals, inits, actions)
