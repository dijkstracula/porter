from porter.ast import Binding, sorts, terms
from porter.passes.quantifiers import BoundExprs

from .bounds import FiniteRange, interval_from_sort_uses


def bounds_for_exists(fmla: terms.Exists) -> list[Binding[FiniteRange]]:
    bound_exprs: list[(Binding[sorts.Sort]), terms.BinOp] = BoundExprs.from_exists(fmla)
    return interval_from_sort_uses(bound_exprs)


def bounds_for_forall(fmla: terms.Forall) -> list[Binding[FiniteRange]]:
    bound_exprs: list[(Binding[sorts.Sort]), terms.BinOp] = BoundExprs.from_forall(fmla)
    return interval_from_sort_uses(bound_exprs)
