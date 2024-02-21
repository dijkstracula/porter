from porter.ast import Binding, sorts, terms
from dataclasses import dataclass
from typing import Optional


@dataclass
class VarBounds:
    var_name: str
    pass


@dataclass
class AppIteration(VarBounds):
    """Represents iterating through all elements of a (presumably!) finite relation, holding certain
    Var arguments constant.  `var_args` is a list of the length of the application's arity - if an
    entry is None, its variable must already be in scope.

    Example: The term `link(X, y)` iterates through all X, but holds some `y` already in the context
    fixed.  So, we'd lift this into: `AppIter(link(...), [Binding('Y', 'y'])`. Presumably
    we will extract this into something akin to: `link.iterate().filter((X, TMP_Y) -> TMP_Y == y)`.

    Example: `r(X, f(X))` should be, I guess, `r.iterate().filter((X, TMP_Y) -> f(X) == TMP_Y)`?

    Example: `r(x, y)` is a point query and doesn't require iteration at all.

    Example: `R(X, y) | R(x, Y)` requires actually iterating through both X and Y, what do?
    """
    app: terms.Apply
    var_args: list[Optional[terms.Var]]


# TODO: Finite range for other finite sorts, like bools and enums.

@dataclass
class NumericInterval(VarBounds):
    """Represents the bounds of a Var that we've observed in a formula.
    For the bounds to be finite, both lo and hi must be non-None. """

    lo: Optional[int | terms.Expr]
    hi: Optional[int | terms.Expr]

    @staticmethod
    def from_binding(b: Binding[sorts.Sort]) -> "NumericInterval":
        name = b.name
        match b.decl:
            case sorts.Uninterpreted(_):
                return NumericInterval(name, None, None)
            case sorts.Number(_, lo_range, hi_range):
                return NumericInterval(name, lo_range, hi_range)
            case _:
                raise Exception(f"{b.decl} isn't a numeric sort?")

    def constrain_lower(self, lo: int) -> "NumericInterval":
        match self.lo:
            case None:
                return NumericInterval(self.var_name, lo, self.hi)
            case curr_lo if isinstance(curr_lo, int):
                return NumericInterval(self.var_name, max(lo, curr_lo), self.hi)
            case terms.Constant(ivy_node, rep) if rep.isnumeric():
                new_lo = terms.Constant(ivy_node, str(max(int(rep), lo)))
                return NumericInterval(self.var_name, new_lo, self.hi)
        return self

    def constrain_upper(self, hi: int) -> "NumericInterval":
        match self.hi:
            case None:
                return NumericInterval(self.var_name, self.lo, hi)
            case curr_hi if isinstance(curr_hi, int):
                return NumericInterval(self.var_name, self.lo, max(hi, curr_hi))
            case terms.Constant(ivy_node, rep) if rep.isnumeric():
                new_hi = terms.Constant(ivy_node, str(max(int(rep), hi)))
                return NumericInterval(self.var_name, self.lo, new_hi)
        return self


def constrain_from_apply(binding: Binding[sorts.Sort], expr: terms.Apply) -> Optional[AppIteration]:
    name = binding.name
    partial_evaled: list[Optional[terms.Expr]] = []
    for arg in expr.args:
        match arg:
            case terms.Constant(_, _):
                partial_evaled.append(None)
            case terms.Var(_, sym):
                if sym == name:
                    partial_evaled.append(arg)
                else:
                    partial_evaled.append(None)
            case _:
                raise Exception(f"TODO: {arg}")
    return AppIteration(name, expr, partial_evaled)


def constraints_from_binop(b: Binding[sorts.Sort], expr: terms.BinOp) -> Optional[NumericInterval]:
    """ If a numeric binop relates `name` to either a literal value or another variable, we want
    to remember that constraint."""

    ret = NumericInterval.from_binding(b)
    match expr:
        case terms.BinOp(_, terms.Var(_, varname), op, terms.Constant(_, rhs_rep)) if varname == b.name:
            if rhs_rep.isnumeric():
                match op:
                    case "<":
                        upper_bound = int(rhs_rep) - 1
                    case "<=":
                        upper_bound = int(rhs_rep)
                    case _:
                        raise Exception(f"Unexpected binop {expr}")
            else:
                upper_bound = expr.rhs
            return ret.constrain_upper(upper_bound)
        case terms.BinOp(_, terms.Constant(_, lhs_rep), op, terms.Var(_, varname)) if varname == b.name:
            if lhs_rep.isnumeric():
                match op:
                    case "<":
                        lower_bound = int(lhs_rep) + 1
                    case "<=":
                        lower_bound = int(lhs_rep)
                    case _:
                        raise Exception(f"Unexpected binop {expr}")
            else:
                lower_bound = expr.lhs
            return ret.constrain_lower(lower_bound)
    return None


def merge_varbounds(vbs: list[VarBounds]) -> list[VarBounds]:
    deduped: dict[str, VarBounds]

    seen = set()
    in_order = []
    for vb in vbs:
        name = vb.var_name
        if not seen[name]:
            seen.add(name)
            in_order.append(deduped[name])
    return in_order


def constraints_from_exprs(exprs: list[(Binding[sorts.Sort], terms.Expr)]) -> list[VarBounds]:
    """ Given a list of (potentially infinite-cardinality) sorts and expressions that potentially constrain their
    range to a finite domain, come up with an interval interval that matches that domain."""
    ret = []
    for binding, expr in exprs:
        match expr:
            case terms.BinOp(_, _, _, _):
                maybe_int = constraints_from_binop(binding, expr)
                if maybe_int:
                    ret.append(maybe_int)
            case terms.Apply(_, _, _):
                maybe_app = constrain_from_apply(binding, expr)
                if maybe_app:
                    ret.append(maybe_app)
            case _:
                raise Exception(f"constraints_from_exprs: {expr}")
    return ret
