from porter.ast import Binding, sorts, terms
from porter.ast.terms.visitor import MutVisitor, Visitor

from enum import Enum
from ivy import ivy_module as imod

from dataclasses import dataclass
from typing import Optional


def inited_to_false(im: imod.Module, ia: terms.Assign) -> bool:
    match ia:
        case terms.Assign(terms.Apply(_, relsym, largs), terms.Constant(_, "false")):
            return relsym in im.destructor_sorts and all([isinstance(arg, terms.Var) for arg in largs])
    return False


def is_point_update(ia: terms.Action) -> bool:
    match ia:
        case terms.Assign(_, terms.Constant(_, _), _rhs):
            return True
    return False


def cardinality(s) -> Optional[int]:
    if hasattr(s, 'card'):
        return s.card
    if s.is_relational():
        return 2
    return None


# ###


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


def interval_from_binops(exprs: list[(Binding[sorts.Sort], terms.BinOp)]) -> list[(Binding[NumericInterval])]:
    """ Given a list of (potentially infinite) sorts and operations that potentially constrain their
    range to a finite domain, coem up with a corresponding finite sort that matches that domain."""
    all_constrained: dict[str, NumericInterval] = {}
    for binding, expr in exprs:
        name = binding.name
        sort = binding.decl
        expr = le_order(expr)  # Possibly redundant to do here
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


def bounds_for_exists(fmla: terms.Exists) -> list[Binding[NumericInterval]]:
    bound_exprs: list[(Binding[sorts.Sort]), terms.BinOp] = BoundExprs.from_exists(fmla)
    return interval_from_binops(bound_exprs)


def bounds_for_forall(fmla: terms.Forall) -> list[Binding[NumericInterval]]:
    bound_exprs: list[(Binding[sorts.Sort]), terms.BinOp] = BoundExprs.from_forall(fmla)
    return interval_from_binops(bound_exprs)


# ###


class Polarity(Enum):
    Forall = 1
    Exists = 2

    @staticmethod
    def flip(p) -> "Polarity":
        match p:
            case Polarity.Forall:
                return Polarity.Exists
            case Polarity.Exists:
                return Polarity.Forall
        raise Exception(p)


class BoundExprs(Visitor[list[terms.BinOp]]):
    """" Finds all the exprs involving a Var within a formula.  Morally, this should do what ivy_to_cpp::get_bound_exprs
    does. """

    @staticmethod
    def from_exists(fmla: terms.Exists) -> list[(Binding[sorts.Sort], terms.BinOp)]:
        ret = []
        for v in fmla.vars:
            nested_visitor = BoundExprs(v, Polarity.Exists)
            pairs = [(v, le_order(expr)) for expr in nested_visitor.visit_expr(fmla.expr)]
            ret.extend(pairs)
        return ret

    @staticmethod
    def from_forall(fmla: terms.Forall) -> list[(Binding[sorts.Sort], terms.BinOp)]:
        ret = []
        for v in fmla.vars:
            nested_visitor = BoundExprs(v, Polarity.Forall)
            pairs = [(v, le_order(expr)) for expr in nested_visitor.visit_expr(fmla.expr)]
            ret.extend(pairs)
        return ret

    #

    v0: str
    pol: Polarity

    def __init__(self, v0: str, pol: Polarity):
        self.v0 = v0
        self.pol = pol

    def flip(self):
        self.pol = Polarity.flip(self.pol)

    def _identifier(self, s: str) -> list[terms.BinOp]:
        return []

    def _begin_apply(self, node: terms.Apply) -> Optional[list[terms.BinOp]]:
        v0_in_use = False
        for arg in node.args:
            match arg:
                case terms.Var(_, rep):
                    if rep == self.v0.name:
                        v0_in_use = True
                        break
        if v0_in_use:
            pass
        return []

    def _begin_binop(self, node: terms.BinOp) -> Optional[list[terms.BinOp]]:
        lhs = []
        rhs = []
        match node.op:
            case "and" if self.pol == Polarity.Exists:
                lhs = self.visit_expr(node.lhs)
                rhs = self.visit_expr(node.rhs)
            case "or" if self.pol == Polarity.Forall:
                lhs = self.visit_expr(node.lhs)
                rhs = self.visit_expr(node.rhs)
            case "implies" if self.pol == Polarity.Forall:
                self.flip()
                lhs = self.visit_expr(node.lhs)
                self.flip()
                rhs = self.visit_expr(node.rhs)
            case cmp if cmp in ["<", "<=", ">", ">="]:
                return [node]
        return lhs + rhs

    def _begin_unop(self, node: terms.UnOp) -> list[terms.BinOp]:
        self.flip()
        ret = self.visit_expr(node.expr)
        self.flip()
        return ret


class NonExtensionals(MutVisitor):
    """Finds all functions such that their uses cannot admit an extensional definition."""

    # Per ivy_to_cpp:
    #     38 # A relation is extensional if:
    #     39 #
    #     40 # 1) It is not derived
    #     41 # 2) It is initialized to all false
    #     42 # 3) Every update is either to a simple point, or to false
    #     43 #
    #
    # TODO: I am not sure how to determine if it's derived.

    im: imod.Module

    exts: set[str]

    def __init__(self, im: imod.Module):
        self.im = im
        self.nons = set()

    def _begin_program(self, prog: terms.Program):
        pass

    def _finish_assign(self, act: terms.Assign, lhs: None, rhs: None):
        act_lhs = act.lhs
        act_rhs = act.rhs
        if not isinstance(act_lhs, terms.Apply):
            return

        relsym = act_lhs.relsym
        args = act_lhs.args

        # relsym cannot be extensional if it is:
        # a) ever initialized to something other than a constant
        if all([isinstance(arg, terms.Var) for arg in args]):
            if not isinstance(act_rhs, terms.Constant):
                self.nons.add(relsym)

        # b) otherwise, ever updated with a non-point lhs
        elif any([isinstance(arg, terms.Var) for arg in args]):
            self.nons.add(relsym)
