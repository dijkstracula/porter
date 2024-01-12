from ivy import ivy_actions as iact
from ivy import ivy_module as imod
from ivy import logic as ilog

from . import compile_toplevel
from typing import Any, Tuple

from porter.ast import terms, sorts

from porter.ivy_shim import expr_from_ivy

import unittest


class ExprTest(unittest.TestCase):
    def compile_annotated_expr(self, sort: str, expr: str) -> Tuple[imod.Module, Any]:
        init_act = "after init { " \
                   f"""var test_expr: {sort} := {expr};
                    var ensure_no_dead_code_elim: {sort} := test_expr;
                    test_expr := ensure_no_dead_code_elim;
                }}"""
        (im, _) = compile_toplevel(init_act)

        action_body = im.initial_actions[0]
        self.assertTrue(isinstance(action_body, iact.LocalAction))
        action_stmts = action_body.args[1]  # "let test_expr := ... in { let ensure... in ... }"
        self.assertTrue(isinstance(action_stmts, iact.Sequence))
        test_expr_assign = action_stmts.args[0]
        self.assertTrue(isinstance(test_expr_assign, iact.AssignAction))
        assign_rhs = test_expr_assign.args[1]
        return im, assign_rhs

    def test_constant(self):
        expr = "42"
        im, compiled = self.compile_annotated_expr("nat", expr)
        self.assertTrue(isinstance(compiled, ilog.Const))

        expr = expr_from_ivy(im, compiled)
        self.assertTrue(isinstance(expr, terms.Constant))

    def test_binop(self):
        expr = "41 + 1"
        im, compiled = self.compile_annotated_expr("nat", expr)
        self.assertTrue(isinstance(compiled, ilog.Apply))

        expr = expr_from_ivy(im, compiled)
        self.assertTrue(isinstance(expr, terms.BinOp))
        self.assertTrue(isinstance(expr.lhs, terms.Constant))
        self.assertTrue(isinstance(expr.rhs, terms.Constant))

    def test_boolean_const(self):
        expr = "true"
        im, compiled = self.compile_annotated_expr("bool", expr)
        self.assertTrue(isinstance(compiled, ilog.And))
        self.assertEqual(len(compiled.clauses), 0)

        expr = expr_from_ivy(im, compiled)
        self.assertTrue(isinstance(expr, terms.Constant))

    def test_boolean_binop(self):
        expr = "false & true & true & false"
        im, compiled = self.compile_annotated_expr("bool", expr)
        self.assertTrue(isinstance(compiled, ilog.And))
        self.assertEqual(len(compiled.args), 4)

        expr = expr_from_ivy(im, compiled)
        self.assertTrue(isinstance(expr, terms.BinOp))
        self.assertEqual(expr.sort(), sorts.Bool())
        self.assertEqual(expr.op, "and")
        self.assertTrue(isinstance(expr.lhs, terms.BinOp))
        self.assertTrue(isinstance(expr.rhs, terms.Constant))
        pass
