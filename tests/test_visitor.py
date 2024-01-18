from porter.ast import Binding, terms
from porter.ast.visitor import Visitor


class ExprCounter(Visitor[None]):
    n_nodes: int = 0

    def constant(self, _rep: str):
        self.n_nodes += 1

    def finish_apply(self, node: terms.Apply, relsym_ret: None, args_ret: list[None]):
        self.n_nodes += 1

    def finish_binop(self, node: terms.BinOp, lhs_ret: None, rhs_ret: None):
        self.n_nodes += 1

    def finish_exists(self, node: terms.Exists, vars: list[Binding[None]], expr: None):
        self.n_nodes += 1

    def finish_forall(self, node: terms.Forall, vars: list[Binding[None]], expr: None):
        self.n_nodes += 1

    def finish_ite(self, node: terms.Ite, test: None, then: None, els: None):
        self.n_nodes += 1

    def finish_some(self, none: terms.Some, vars: list[Binding[None]], fmla: None):
        self.n_nodes += 1

    def finish_unop(self, node: terms.UnOp, expr: None):
        self.n_nodes += 1

def test_expr_visitation():
    ast = terms.BinOp(
        None,
        terms.Constant(None, "42"),
        "+",
        terms.Constant(None, "42"))

    visitor = ExprCounter()
    visitor.visit_expr(ast)
    assert visitor.n_nodes == 3
