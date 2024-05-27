from porter.ast import terms
from porter.ast.terms.visitor import MutVisitor

from ivy import ivy_module as imod


def inited_to_const(rhs: terms.Expr, args: list[terms.Expr]) -> bool:
    """A map cannot be extensional if it is ever initialized to something other
    than a constant"""
    if all([isinstance(arg, terms.Var) for arg in args]):
        return isinstance(rhs, terms.Constant)
    return False



def is_point_update(args: list[terms.Expr]) -> bool:
    """A map cannot be extensional if it is ever updated with a logical variable"""

    # XXX: Technically, shouldn't this walk all the exprs and see if a Var
    # resides in the AST somewhere?
    if any([isinstance(arg, terms.Var) for arg in args]):
        return False
    return True


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

    def __init__(self, im: imod.Module):
        self.im = im
        self.nons = set()

    def _begin_program(self, prog: terms.Program):
        pass

    def _finish_logical_assign(self, act: terms.LogicalAssign, relsym, args, assn):
        relsym = act.relsym
        args = act.vars
        rhs = act.assign

        # relsym cannot be extensional if it is:
        # a) ever initialized to something other than a constant
        if not inited_to_const(rhs, args):
            self.nons.add(relsym)

        # b) otherwise, ever updated with a non-point lhs
        elif not is_point_update(args):
            self.nons.add(relsym)


    def _finish_assign(self, act: terms.Assign, lhs: None, rhs: None):
        act_lhs = act.lhs
        act_rhs = act.rhs
        if not isinstance(act_lhs, terms.Apply):
            return

        relsym = act_lhs.relsym
        args = act_lhs.args

        # relsym cannot be extensional if it is:
        # a) ever initialized to something other than a constant
        if not inited_to_const(act_rhs, args):
            self.nons.add(relsym)

        # b) otherwise, ever updated with a non-point lhs
        if not is_point_update(args):
            self.nons.add(relsym)
