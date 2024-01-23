from ivy import ivy_ast as iast
from ivy import ivy_module as imod
from ivy import logic as ilog

from . import compile_annotated_expr

from porter.ast import terms, sorts

from porter.ivy_shim import expr_from_ivy

import unittest


class ExprTest(unittest.TestCase):

    def test_constant(self):
        expr = "42"
        im, compiled = compile_annotated_expr("nat", expr)
        self.assertTrue(isinstance(compiled, ilog.Const))

        expr = expr_from_ivy(im, compiled)
        self.assertTrue(isinstance(expr, terms.Constant))

    def test_binop(self):
        expr = "41 + 1"
        im, compiled = compile_annotated_expr("nat", expr)
        self.assertTrue(isinstance(compiled, ilog.Apply))

        expr = expr_from_ivy(im, compiled)
        assert isinstance(expr, terms.BinOp)
        self.assertTrue(isinstance(expr.lhs, terms.Constant))
        self.assertTrue(isinstance(expr.rhs, terms.Constant))

    def test_boolean_true(self):
        expr = "true"
        im, compiled = compile_annotated_expr("bool", expr)
        self.assertTrue(isinstance(compiled, ilog.And))
        self.assertEqual(len(compiled.args), 0)

        expr = expr_from_ivy(im, compiled)
        self.assertTrue(isinstance(expr, terms.Constant))

    def test_boolean_false(self):
        expr = "false"
        im, compiled = compile_annotated_expr("bool", expr)
        self.assertTrue(isinstance(compiled, ilog.Or))
        self.assertEqual(len(compiled.args), 0)

        expr = expr_from_ivy(im, compiled)
        self.assertTrue(isinstance(expr, terms.Constant))

    def test_boolean_binop(self):
        expr = "false & true & true & false"
        im, compiled = compile_annotated_expr("bool", expr)
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
        self.assertEqual(expr.relsym, terms.Constant(None, "inc"))
