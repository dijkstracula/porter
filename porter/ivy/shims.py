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
from ivy import ivy_utils as iu

from porter.ast import Binding, sorts, terms
from porter.ast.terms.visitor import SortVisitorOverTerms
from porter.passes import native_rewriter
from porter.passes.reinterpret_uninterps import InterpretUninterpretedVisitor

from . import members


def compile_progtext(path: Path) -> iart.AnalysisGraph:
    logging.info(f"Compiling {path}")

    cwd = os.getcwd()
    os.chdir(path.parent)
    with open(path) as f:
        with iu.SourceFile(path):
            ic.ivy_load_file(f, create_isolate=False)
            iiso.create_isolate('this')
        os.chdir(cwd)
    return ic.ivy_new()


def handle_isolate(path: Path) -> terms.Program:
    with imod.Module() as im:
        compile_progtext(path)
        return program_from_ivy(im)


def binding_from_ivy_var(im: imod.Module, v: ilog.Var) -> Binding[sorts.Sort]:
    name = v.rep
    sort = sorts.from_ivy(v.sort)
    return Binding(name, sort)


def binding_from_ivy_const(im: imod.Module, c: ilog.Const) -> Binding[sorts.Sort]:
    name = c.name
    sort = sorts.from_ivy(c.sort)
    return Binding(name, sort)


# Expression conversion

def expr_from_apply(im: imod.Module, app: ilog.Apply) -> terms.Expr:
    if app.func.name in ['+', "-", "<=", "<", ">", ">="]:
        lhs = expr_from_ivy(im, app.args[0])
        rhs = expr_from_ivy(im, app.args[1])
        return terms.BinOp(app, lhs, app.func.name, rhs)
    func = app.func.name  # expr_from_ivy(im, app.args[0])
    args = [expr_from_ivy(im, a) for a in app.args]

    return terms.Apply(app, func, args)


def expr_from_const(_im: imod.Module, c: ilog.Const) -> terms.Constant:
    return terms.Constant(c, c.name)


def expr_from_var(_im: imod.Module, v: ilog.Var) -> terms.Var:
    return terms.Var(v, v.name)


def expr_from_atom(im: imod.Module, expr: iast.Atom) -> terms.Apply:
    args = [expr_from_ivy(im, a) for a in expr.args]
    return terms.Apply(expr, expr.rep, args)


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
    return terms.UnOp(expr, "~", lhs)


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
    variables = [binding_from_ivy_const(im, c) for c in fmla.variables]
    body = expr_from_ivy(im, fmla.body)
    return terms.Exists(fmla, variables, body)


def expr_from_forall(im: imod.Module, fmla: ilog.Exists) -> terms.Forall:
    variables = [binding_from_ivy_const(im, c) for c in fmla.variables]
    body = expr_from_ivy(im, fmla.body)
    return terms.Forall(fmla, variables, body)


def expr_from_native(im: imod.Module, expr: iast.NativeExpr) -> terms.NativeExpr:
    code = str(expr.args[0])
    args = [expr_from_ivy(im, a) for a in expr.args[1:]]
    return terms.NativeExpr(expr, "c++", code, args)


def expr_binding_from_labeled_formula(im: imod.Module, fmla: iast.LabeledFormula) -> Binding[terms.Expr]:
    assert isinstance(fmla.label, iast.Atom)
    name = fmla.label.rep
    decl = expr_from_ivy(im, fmla.formula)
    decl._ivy_node = fmla
    return Binding(name, decl)


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

    variables = [binding_from_ivy_const(im, c) for c in expr.args[0:-1]]
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
    if isinstance(expr, iast.LabeledFormula):
        # XXX: Hacky.  Is it fine to throw out the label?
        return expr_from_ivy(im, expr.args[1])

    # Ternary operators
    if isinstance(expr, ilog.Ite):
        return expr_from_ite(im, expr)

    # TODOs
    if isinstance(expr, iast.NativeExpr):
        return expr_from_native(im, expr)
    if isinstance(expr, iast.Some):
        return expr_from_some(im, expr)

    raise Exception(f"TODO: {expr} ({type(expr)})")


# Action/statement conversion


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


def assert_from_ivy(im: imod.Module, iaction: iact.AssertAction) -> terms.Assert:
    pred = expr_from_ivy(im, iaction.args[0])
    return terms.Assert(iaction, pred)


def assign_from_ivy(im: imod.Module, iaction: iact.AssignAction) -> terms.Action:
    lhs = expr_from_ivy(im, iaction.args[0])
    rhs = expr_from_ivy(im, iaction.args[1])
    assn = terms.Assign(iaction, lhs, rhs)

    # if the LHS contains an (implicitly-declared) Var, then this means
    # we have to lift the assign into a LogicalAssign.
    lassn = terms.LogicalAssign.maybe_from_assign(assn)
    if lassn is not None:
        return lassn
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


def havok_from_ivy(im: imod.Module, iaction: iact.HavocAction) -> terms.Havok:
    with im:
        modifies = [expr_from_ivy(im, m) for m in iaction.modifies()]
    return terms.Havok(iaction, modifies)


def local_from_ivy(im: imod.Module, iaction: iact.LocalAction) -> terms.Let:
    varnames = [binding_from_ivy_const(im, c) for c in iaction.args[:-1]]
    act = action_from_ivy(im, iaction.args[-1])
    return terms.Let(im, varnames, act)


def native_act_from_ivy(im: imod.Module, iaction: iact.NativeAction) -> terms.NativeAct:
    code = str(iaction.args[0])
    args = [expr_from_ivy(im, a) for a in iaction.args[1:]]
    return terms.NativeAct(iaction, "c++", code, args)


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
    if isinstance(act, iact.HavocAction):
        return havok_from_ivy(im, act)
    if isinstance(act, iact.LocalAction):
        return local_from_ivy(im, act)
    if isinstance(act, iact.NativeAction):
        return native_act_from_ivy(im, act)
    if isinstance(act, iact.Sequence):
        subacts = [action_from_ivy(im, a) for a in act.args]
        if len(subacts) == 1:
            return subacts[0]
        return terms.Sequence(act, subacts)

    raise Exception(f"TODO: {type(act)}")


def action_kind_from_name(name: str) -> terms.ActionKind:
    if name.startswith("ext:"):
        return terms.ActionKind.EXPORTED
    if name.startswith("imp"):
        return terms.ActionKind.IMPORTED
    return terms.ActionKind.NORMAL


def action_def_from_ivy(im: imod.Module, name: str, iaction: iact.Action) -> terms.ActionDefinition:
    kind = action_kind_from_name(name)
    assert (hasattr(iaction, "formal_params"))
    formal_params = [binding_from_ivy_const(im, p) for p in iaction.formal_params]
    formal_returns = [binding_from_ivy_const(im, p) for p in iaction.formal_returns]
    body = action_from_ivy(im, iaction)

    return terms.ActionDefinition(iaction, kind, formal_params, formal_returns, body)


def function_def_from_ivy(im: imod.Module, defn: iast.Definition) -> terms.FunctionDefinition:
    kind = terms.ActionKind.NORMAL

    # We have to do some light surgery to mangle a function definition into FunctionDefinition.
    # The Ivy Function definition is a tuple of def(arg1, arg2, ...) iff P(arg1, arg2, ...).
    # So, we extract the function name and argument bindings from the lhs, and the "body" of the
    # function is the RHS.
    #
    # It's possible that if we treat extensional functions and "computational functions" as equivalent
    # then we can simplify a lot of this.

    lhs = expr_from_ivy(im, defn.args[0])
    assert isinstance(lhs, terms.Apply)

    formal_params = []
    for p in lhs.args:
        match p:
            case terms.Constant(_, rep) | terms.Var(_, rep):
                formal_params.append(Binding(rep, p.sort()))
            case _:
                raise Exception(f"Unex: {p}")

    rhs = expr_from_ivy(im, defn.args[1])

    ret = terms.FunctionDefinition(defn.args[0].rep, formal_params, rhs)

    # One more piece of surgery: for some reason, NativeExpr's types are Top (presumably because we can't actually
    # typecheck its contents!)
    if isinstance(rhs, terms.NativeExpr):
        s = ret.sort()
        assert isinstance(s, sorts.Function)
        rhs._sort = s.range

    return ret


def program_from_ivy(im: imod.Module) -> terms.Program:
    porter_sorts = {}
    for name, ivy_sort in list(im.sig.sorts.items()) + list(im.native_types.items()):
        if name in im.sig.interp and not isinstance(im.sig.interp[name], str):
            # XXX: why should the values of im.sig.interp ever not be a Sort?
            porter_sort = sorts.from_ivy(im.sig.interp[name])
        elif name in im.sort_destructors:
            porter_sort = sorts.record_from_ivy(im, name)
        else:
            porter_sort = sorts.from_ivy(ivy_sort)
        porter_sorts[name] = porter_sort
    vardecls = [binding_from_ivy_const(im, sym) for sym in members(im)]
    inits = [action_from_ivy(im, a) for a in im.initial_actions]

    actions = []
    for name, ivy_act in im.actions.items():
        actions.append(Binding(name, action_def_from_ivy(im, name, ivy_act)))

    conjs = [expr_binding_from_labeled_formula(im, b) for b in im.labeled_conjs]

    defns = []
    for lf in im.definitions + im.native_definitions:
        name = lf.formula.defines().name
        if name == "<":  # HACK
            continue
        defns.append(Binding(name, function_def_from_ivy(im, lf.formula)))

    # At this point, Records are going to marked as bound but typed as Uninterpreted.
    # Do a pass to patch those up.
    # Seems like we have a similar problem with Natives.  (TODO: what else???)
    to_remap: dict[str, sorts.Sort] = {name: sorts.record_from_ivy(im, name) for name in im.sort_destructors}
    to_remap.update({name: sort for name, sort in porter_sorts.items() if isinstance(sort, sorts.Native)})
    # TODO: also walk sig.interp, but that mapping's values are not well typed so I don't know how to handle them yet.

    prog = terms.Program(im, porter_sorts, vardecls, inits, actions, defns, conjs)

    reinterp = SortVisitorOverTerms(InterpretUninterpretedVisitor(to_remap))
    reinterp.visit_program(prog)
    reinterp.visit_program_sorts(prog, reinterp.sort_visitor)

    native_rewriter.visit(prog)

    return prog
