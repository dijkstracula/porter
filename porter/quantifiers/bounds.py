from porter.ast import Binding, sorts, terms
from porter.ast.terms.visitor import MutVisitor, Visitor

from enum import Enum
from ivy import ivy_module as imod

from dataclasses import dataclass
from typing import Optional


@dataclass
class FiniteRange:
    pass


# TODO: Finite range for other finite sorts, like bools and enums.

@dataclass
class NumericInterval(FiniteRange):
    lo: Optional[int | terms.Constant | terms.Var]
    hi: Optional[int | terms.Constant | terms.Var]

    @staticmethod
    def from_sort(s: sorts.Sort) -> "NumericInterval":
        match s:
            case sorts.Uninterpreted(_):
                return NumericInterval(None, None)
            case sorts.Number(_, lo_range, hi_range):
                return NumericInterval(lo_range, hi_range)
            case _:
                raise Exception(f"{s} isn't a numeric sort?")

    def constrain_lower(self, lo: int) -> "NumericInterval":
        match self.lo:
            case None:
                return NumericInterval(lo, self.hi)
            case curr_lo if isinstance(curr_lo, int):
                return NumericInterval(max(lo, curr_lo), self.hi)
            case terms.Constant(ivy_node, rep) if rep.isnumeric():
                new_lo = terms.Constant(ivy_node, str(max(int(rep), lo)))
                return NumericInterval(new_lo, self.hi)
        return self

    def constrain_upper(self, hi: int) -> "NumericInterval":
        match self.hi:
            case None:
                return NumericInterval(self.lo, hi)
            case curr_hi if isinstance(curr_hi, int):
                return NumericInterval(self.lo, max(hi, curr_hi))
            case terms.Constant(ivy_node, rep) if rep.isnumeric():
                new_hi = terms.Constant(ivy_node, str(max(int(rep), hi)))
                return NumericInterval(self.lo, new_hi)
        return self


def le_order(s: terms.BinOp) -> terms.BinOp:
    match s.op:
        case "<" | "<=":
            return s
        case ">":
            return terms.BinOp(s._ivy_node, s.rhs, "<", s.lhs)
        case ">=":
            return terms.BinOp(s._ivy_node, s.rhs, "<=", s.lhs)
        case _:
            raise Exception("Not an ordered binop")


def interval_from_sort_uses(exprs: list[(Binding[sorts.Sort], terms.BinOp | terms.Apply)]) -> list[
    (Binding[FiniteRange])]:
    """ Given a list of (potentially infinite) sorts and expressions that potentially constrain their
    range to a finite domain, come up with a corresponding finite interval that matches that domain."""
    all_constrained: dict[str, FiniteRange] = {}
    for binding, expr in exprs:
        name = binding.name
        sort = binding.decl
        expr = le_order(expr)  # But only if it's a BinOp!
        match expr:
            case terms.BinOp(_, terms.Var(_, lhs), op, terms.Constant(_, rhs)) if lhs == name and rhs.isnumeric():
                match op:
                    case "<":
                        upper_bound = int(rhs) - 1
                    case "<=":
                        upper_bound = int(rhs)
                    case _:
                        raise Exception(f"Unexpected binop {expr}")

                if name not in all_constrained:
                    all_constrained[name] = NumericInterval.from_sort(sort).constrain_upper(upper_bound)
                else:
                    all_constrained[name] = all_constrained[name].constrain_upper(upper_bound)
            case terms.BinOp(_, terms.Constant(_, lhs), op, terms.Var(_, rhs)) if rhs == name and lhs.isnumeric():
                match op:
                    case "<":
                        lower_bound = int(lhs) + 1
                    case "<=":
                        lower_bound = int(lhs)
                    case _:
                        raise Exception(f"Unexpected binop {expr}")

                if name not in all_constrained:
                    all_constrained[name] = NumericInterval.from_sort(sort).constrain_lower(lower_bound)
                else:
                    all_constrained[name] = all_constrained[name].constrain_lower(lower_bound)

    # Return the output list with the same order as the input one, except that we deduplicate
    # bindings (since we've merged them together already)
    seen = set()
    ret = []
    for b, _ in exprs:
        if b.name not in seen:
            seen.add(b.name)
            ret.append(Binding(b.name, all_constrained[b.name]))
    return ret
