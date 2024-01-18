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


def expr_from_atom(im: imod.Module, expr: iast.Atom) -> terms.Apply:
    relsym = expr.rep
    args = [expr_from_ivy(im, a) for a in expr.args]
    return terms.Apply(expr, relsym, args)


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


def expr_from_iff(im: imod.Module, expr: ilog.Iff) -> terms.BinOp:
    ltor = expr_from_ivy(im, expr.args[0])
    rtol = expr_from_ivy(im, expr.args[1])
    return terms.BinOp(expr, ltor, "iff", rtol)


def expr_from_exists(im: imod.Module, fmla: ilog.Exists) -> terms.Exists:
    variables = [binding_from_ivy_const(c) for c in fmla.variables]
    body = expr_from_ivy(im, fmla.body)
    return terms.Exists(fmla, variables, body)


def expr_from_forall(im: imod.Module, fmla: ilog.Exists) -> terms.Forall:
    variables = [binding_from_ivy_const(c) for c in fmla.variables]
    body = expr_from_ivy(im, fmla.body)
    return terms.Forall(fmla, variables, body)


def expr_from_ite(im: imod.Module, ite: ilog.Ite) -> terms.Ite:
    test = expr_from_ivy(im, ite.args[0])
    then = expr_from_ivy(im, ite.args[1])
    els = expr_from_ivy(im, ite.args[2])
    return terms.Ite(ite, test, then, els)


def expr_from_some(im: imod.Module, expr: iast.Some) -> terms.Some:
    if isinstance(expr, iast.SomeMin):
        strat = terms.SomeStrategy.MINIMISE
    elif isinstance(expr, iast.SomeMax):
        strat = terms.SomeStrategy.MAXIMISE
    else:
        strat = terms.SomeStrategy.ARBITRARY

    variables = [binding_from_ivy_const(c) for c in expr.args[0:-1]]
    fmla = expr_from_ivy(im, expr.args[-1])
    return terms.Some(expr, variables, fmla, strat)


def expr_from_ivy(im: imod.Module, expr) -> terms.Expr:
    # Terminals
    if isinstance(expr, ilog.Const):
        return expr_from_const(im, expr)
    if isinstance(expr, ilog.Var):
        return expr_from_var(im, expr)

    # Application
    if isinstance(expr, ilog.Apply):
        return expr_from_apply(im, expr)

    # Binops
    if isinstance(expr, ilog.And):
        return expr_from_and(im, expr)
    if isinstance(expr, ilog.Or):
        return expr_from_or(im, expr)
    if isinstance(expr, ilog.Implies):
        return expr_from_implies(im, expr)
    if isinstance(expr, ilog.Iff):
        return expr_from_iff(im, expr)
    if isinstance(expr, ilog.Eq):
        return expr_from_eq(im, expr)

    # Unary ops
    if isinstance(expr, ilog.Not):
        return expr_from_not(im, expr)

    # Logic
    if isinstance(expr, iast.Atom):
        return expr_from_atom(im, expr)
    if isinstance(expr, ilog.Exists):
        return expr_from_exists(im, expr)
    if isinstance(expr, ilog.ForAll):
        return expr_from_forall(im, expr)

    if isinstance(expr, ilog.Ite):
        return expr_from_ite(im, expr)

    # TODOs
    if isinstance(expr, iast.Some):
        return expr_from_some(im, expr)

    raise Exception(f"TODO: {expr} ({type(expr)})")


# Action/statement conversion


def action_kind_from_name(name: str) -> terms.ActionKind:
    if name.startswith("ext:"):
        return terms.ActionKind.EXPORTED
    if name.startswith("imp"):
        return terms.ActionKind.IMPORTED
    return terms.ActionKind.NORMAL


def if_from_ivy(im: imod.Module, iaction: iact.IfAction) -> terms.If:
    cond = expr_from_ivy(im, iaction.args[0])
    then = action_from_ivy(im, iaction.args[1])
    if len(iaction.args) > 2:
        els = action_from_ivy(im, iaction.args[2])
    else:
        els = None
    return terms.If(iaction, cond, then, els)


def while_from_ivy(im: imod.Module, iaction: iact.WhileAction) -> terms.While:
    cond = expr_from_ivy(im, iaction.args[0])
    body = action_from_ivy(im, iaction.args[1])
    if len(iaction.args) > 2:
        # Slightly hacky but I can't be bothered to create an ast node for a Ranking yet.
        measure = expr_from_ivy(im, iaction.args[2].args[0])
    else:
        measure = None
    return terms.While(iaction, cond, measure, body)


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
    kind = action_kind_from_name(name)

    return terms.ActionDefinition(iaction, kind, formal_params, formal_returns, body)


def assert_from_ivy(im: imod.Module, iaction: iact.AssumeAction) -> terms.Assert:
    pred = expr_from_ivy(im, iaction.args[0])
    return terms.Assert(im, pred)


def assign_from_ivy(im: imod.Module, iaction: iact.AssignAction) -> terms.Assign:
    lhs = expr_from_ivy(im, iaction.args[0])
    rhs = expr_from_ivy(im, iaction.args[1])
    return terms.Assign(iaction, lhs, rhs)


def assume_from_ivy(im: imod.Module, iaction: iact.AssumeAction) -> terms.Assume:
    pred = expr_from_ivy(im, iaction.args[0])
    return terms.Assume(im, pred)


def call_from_ivy(im: imod.Module, iaction: iact.CallAction) -> terms.Action:
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


def debug_from_ivy(im: imod.Module, iaction: iact.DebugAction) -> terms.Debug:
    msg = repr(iaction.args[0])
    args = [Binding(di.args[0], expr_from_ivy(im, di.args[1])) for di in iaction.args[1:]]
    return terms.Debug(iaction, msg, args)


def local_from_ivy(im: imod.Module, iaction: iact.LocalAction) -> terms.Let:
    varnames = [binding_from_ivy_const(c) for c in iaction.args[:-1]]
    act = action_from_ivy(im, iaction.args[-1])
    return terms.Let(im, varnames, act)


def native_from_ivy(im: imod.Module, iaction: iact.NativeAction) -> terms.Native:
    code = str(iaction.args[0])
    args = [expr_from_ivy(im, a) for a in iaction.args[1:]]
    return terms.Native(iaction, code, args)


def action_from_ivy(im: imod.Module, act: iact.Action) -> terms.Action:
    if isinstance(act, iact.IfAction):
        return if_from_ivy(im, act)
    if isinstance(act, iact.WhileAction):
        return while_from_ivy(im, act)

    if isinstance(act, iact.AssignAction):
        return assign_from_ivy(im, act)
    if isinstance(act, iact.AssumeAction):
        return assume_from_ivy(im, act)
    if isinstance(act, iact.AssertAction):
        return assert_from_ivy(im, act)
    if isinstance(act, iact.CallAction):
        return call_from_ivy(im, act)
    if isinstance(act, iact.DebugAction):
        return debug_from_ivy(im, act)
    if isinstance(act, iact.LocalAction):
        return local_from_ivy(im, act)
    if isinstance(act, iact.NativeAction):
        return native_from_ivy(im, act)
    if isinstance(act, iact.Sequence):
        subacts = [action_from_ivy(im, a) for a in act.args]
        if len(subacts) == 1:
            return subacts[0]
        return terms.Sequence(act, subacts)

    if isinstance(act, iact.HavocAction):
        return None  # XXX: Hole

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
