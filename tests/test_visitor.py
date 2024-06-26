from porter.ast import Binding, sorts, terms
from porter.ast.terms.visitor import Visitor, ImmutVisitor

from .test_programs import compile_and_parse, unit_tests

import pytest

from typing import Optional


class ExprCounter(Visitor[None]):
    n_expr_nodes: int = 0
    n_action_nodes: int = 0

    # Expressions

    def _identifier(self, _s: str):
        self.n_expr_nodes += 1

    def _finish_apply(self, node: terms.Apply, relsym_ret: None, args_ret: list[None]):
        self.n_expr_nodes += 1

    def _finish_binop(self, node: terms.BinOp, lhs_ret: None, rhs_ret: None):
        self.n_expr_nodes += 1

    def _finish_exists(self, node: terms.Exists, vs: list[Binding[None]], expr: None):
        self.n_expr_nodes += 1

    def _finish_field_access(self, node: terms.FieldAccess, struct: None, name: None):
        self.n_expr_nodes += 1

    def _finish_forall(self, node: terms.Forall, vs: list[Binding[None]], expr: None):
        self.n_expr_nodes += 1

    def _finish_ite(self, node: terms.Ite, test: None, then: None, els: None):
        self.n_expr_nodes += 1

    def _finish_native_expr(self, node: terms.NativeExpr, args: list[None]) -> None:
        self.n_expr_nodes += 1

    def _finish_some(self, none: terms.Some, vs: list[Binding[None]], fmla: None):
        self.n_expr_nodes += 1

    def _finish_unop(self, node: terms.UnOp, expr: None):
        self.n_expr_nodes += 1

    # Actions

    def _finish_assert(self, act: terms.Assert, pred: None):
        self.n_action_nodes += 1

    def _finish_assign(self, act: terms.Assign, lhs: None, rhs: None):
        self.n_action_nodes += 1

    def _finish_assume(self, act: terms.Assume, pred: None):
        self.n_action_nodes += 1

    def _finish_call(self, act: terms.Call, app: None):
        self.n_action_nodes += 1

    def _finish_debug(self, act: terms.Debug, args: list[None]):
        self.n_action_nodes += 1

    def _finish_ensures(self, act: terms.Ensures, pred: None):
        self.n_action_nodes += 1

    def _finish_havok(self, act: terms.Havok, modifies: list[None]):
        self.n_action_nodes += 1

    def _finish_if(self, act: terms.If, test: None, then: list[None], els: Optional[None]):
        self.n_action_nodes += 1

    def _finish_init(self, act: terms.Init, act_t: None):
        self.n_action_nodes += 1

    def _finish_let(self, act: terms.Let, scope: None):
        self.n_action_nodes += 1

    def _finish_logical_assign(self, act: terms.LogicalAssign, relsym, args, assn):
        self.n_action_nodes += 1

    def _finish_native_action(self, act: terms.NativeAct, args: list[None]):
        self.n_action_nodes += 1

    def _finish_sequence(self, act: terms.Sequence, stmts: list[None]):
        self.n_action_nodes += 1

    def _finish_action_def(self,
                           name: str,
                           defn: terms.ActionDefinition,
                           action: None) -> None:
        pass

    def _finish_function_def(self,
                             name: str,
                             defn: terms.FunctionDefinition,
                             action: None) -> None:
        pass


def test_simple_expr():
    ast = terms.BinOp(
        None,
        terms.Constant(None, "42"),
        "+",
        terms.Constant(None, "42"))

    visitor = ExprCounter()
    visitor.visit_expr(ast)
    assert visitor.n_expr_nodes == 3


@pytest.mark.parametrize("fn", unit_tests)
def test_visit_program(fn):
    ast = compile_and_parse(fn)
    visitor = ExprCounter()
    visitor.visit_program(ast)  # Just ensure we don't throw an unimplemented node exception


@pytest.mark.parametrize("fn", unit_tests)
def test_immut_visitor(fn):
    ast = compile_and_parse(fn)

    class NoOpImmutVisitor(ImmutVisitor):
        pass

    visitor = NoOpImmutVisitor()

    visitor.visit_program(ast)

    assert visitor.actions == ast.actions
    assert visitor.functions == ast.functions
    assert visitor.inits == ast.inits
    assert visitor.individuals == ast.individuals
