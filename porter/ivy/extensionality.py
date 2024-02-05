from porter.ast import terms
from porter.ast.terms.visitor import MutVisitor

from ivy import ivy_module as imod

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


def sort_has_domain(sort) -> bool:
    if not hasattr(sort, "dom"):
        return False
    return len(sort.dom) > 0


def cardinality(s) -> Optional[int]:
    if hasattr(s, 'card'):
        return s.card
    if s.is_relational():
        return 2
    return None


# Per ivy_to_cpp:
#     38 # A relation is extensional if:
#     39 #
#     40 # 1) It is not derived
#     41 # 2) It is initialized to all false
#     42 # 3) Every update is either to a simple point, or to false
#     43 #
#
# TODO: I am not sure how to determine if it's derived.


class NonExtensionals(MutVisitor):
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

