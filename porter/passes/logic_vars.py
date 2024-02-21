from porter.ast import terms
from porter.ast.terms import Var
from porter.ast.terms.visitor import MutVisitor, Visitor


class FreeVars(MutVisitor):
    "Accumulates all free Vars in an AST."

    vars: set[str]

    def __init__(self):
        self.vars = set()

    def _var(self, v: Var):
        if not self._in_scope(v.rep):
            self.vars.add(v.rep)


class BindVar(Visitor[terms.Expr]):
    "Binds a given Var within an Expression (that is, just turns it into a non-logical Constant with the same rep.)"
    bound_var: str

    def __init__(self, v: str):
        self.bound_var = v

    def _identifier(self, s: str) -> terms.Expr:
        # This is only ever discarded, but we need to have an implementation.
        return terms.Constant(None, "<internal_unused>")

    def _constant(self, c: terms.Constant) -> terms.Constant:
        return c

    def _var(self, v: terms.Var) -> terms.Var:
        if v.rep == self.bound_var:
            return terms.Constant(v._ivy_node, self.bound_var)
        return v

    def _finish_binop(self, node: terms.BinOp, lhs_ret: terms.Expr, rhs_ret: terms.Expr) -> terms.BinOp:
        return terms.BinOp(node._ivy_node, lhs_ret, node.op, rhs_ret)

    def _finish_apply(self, node: terms.Apply, _unused: terms.Expr, args_ret: list[terms.Expr]) -> terms.Apply:
        return terms.Apply(node._ivy_node, node.relsym, args_ret)
