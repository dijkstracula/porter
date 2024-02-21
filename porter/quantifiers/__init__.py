from porter.ast import Binding, sorts, terms
from porter.passes.quantifiers import BoundExprs
from porter.ast.terms.visitor import MutVisitor

from ivy import ivy_module as imod

from .bounds import VarBounds, constraints_from_exprs


def bounds_for_exists(fmla: terms.Exists) -> list[Binding[VarBounds]]:
    bound_exprs: list[(Binding[sorts.Sort]), terms.Expr] = BoundExprs.from_exists(fmla)

    return constraints_from_exprs(bound_exprs)


def bounds_for_forall(fmla: terms.Forall) -> list[Binding[VarBounds]]:
    bound_exprs: list[(Binding[sorts.Sort]), terms.Expr] = BoundExprs.from_forall(fmla)
    return constraints_from_exprs(bound_exprs)
