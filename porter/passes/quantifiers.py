from porter.ast import Binding, sorts, terms
from porter.ast.terms.visitor import Visitor

from enum import Enum

from typing import Optional


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


class BoundExprs(Visitor[list[terms.Expr]]):
    """" Finds all the exprs involving a Var within a formula.  Morally, this should do what ivy_to_cpp::get_bound_exprs
    does. """

    @staticmethod
    def from_exists(fmla: terms.Exists) -> list[tuple[Binding[sorts.Sort], terms.Expr]]:
        ret = []
        free_vars = fmla.vars
        for b in free_vars:
            nested_visitor = BoundExprs(b.name, Polarity.Exists)
            pairs = [(b, expr) for expr in nested_visitor.visit_expr(fmla.expr)]
            ret.extend(pairs)
        return ret

    @staticmethod
    def from_forall(fmla: terms.Forall) -> list[tuple[Binding[sorts.Sort], terms.Expr]]:
        ret = []
        for b in fmla.vars:
            # TODO: a thing I need to do in the nested visitor is turn b into a Constant!
            nested_visitor = BoundExprs(b.name, Polarity.Forall)
            pairs = [(b, expr) for expr in nested_visitor.visit_expr(fmla.expr)]
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

    def _identifier(self, s: str) -> list[terms.Expr]:
        return []

    def _begin_apply(self, node: terms.Apply) -> Optional[list[terms.Expr]]:
        # XXX: The fact that I have to do this intead of `if v0 in node.args` suggests
        # an impedence mismatch somewhere...
        for arg in node.args:
            match arg:
                case terms.Var(_, rep):
                    if rep == self.v0:
                        return [node]
        return []

    def _begin_binop(self, node: terms.BinOp) -> Optional[list[terms.Expr]]:
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
                return [le_order(node)]
        return lhs + rhs

    def _begin_unop(self, node: terms.UnOp) -> list[terms.Expr]:
        self.flip()
        ret = self.visit_expr(node.expr)
        self.flip()
        return ret
