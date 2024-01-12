from ivy import ivy_actions as iact
from ivy import ivy_ast as iast
from ivy import ivy_module as imod
from ivy import logic as ilog

from . import compile_toplevel, extract_after_init
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

        test_expr_assign = extract_after_init(im).args[0]
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
        assert isinstance(expr, terms.BinOp)
        self.assertTrue(isinstance(expr.lhs, terms.Constant))
        self.assertTrue(isinstance(expr.rhs, terms.Constant))

    def test_boolean_true(self):
        expr = "true"
        im, compiled = self.compile_annotated_expr("bool", expr)
        self.assertTrue(isinstance(compiled, ilog.And))
        self.assertEqual(len(compiled.args), 0)

        expr = expr_from_ivy(im, compiled)
        self.assertTrue(isinstance(expr, terms.Constant))

    def test_boolean_false(self):
        expr = "false"
        im, compiled = self.compile_annotated_expr("bool", expr)
        self.assertTrue(isinstance(compiled, ilog.Or))
        self.assertEqual(len(compiled.args), 0)

        expr = expr_from_ivy(im, compiled)
        self.assertTrue(isinstance(expr, terms.Constant))

    def test_boolean_binop(self):
        expr = "false & true & true & false"
        im, compiled = self.compile_annotated_expr("bool", expr)
        self.assertTrue(isinstance(compiled, ilog.And))
        self.assertEqual(len(compiled.args), 4)

        expr = expr_from_ivy(im, compiled)
        assert isinstance(expr, terms.BinOp)
        self.assertEqual(expr.sort(), sorts.Bool())
        self.assertEqual(expr.op, "and")
        self.assertTrue(isinstance(expr.lhs, terms.BinOp))
        self.assertTrue(isinstance(expr.rhs, terms.Constant))
        pass

    def test_atom(self):
        ivy_expr = iast.Atom("inc", ilog.Const("42", ilog.UninterpretedSort("nat")))
        expr = expr_from_ivy(imod.Module, ivy_expr)
        assert isinstance(expr, terms.Apply)
        self.assertEquals(expr.relsym, "inc")
