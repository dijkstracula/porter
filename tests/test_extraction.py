from porter.ivy import shims
from porter.ast import Binding, terms
from porter.pp.formatter import Naive
from porter.extraction import java

from . import compile_annotated_expr

import unittest


class JavaExtractionTests(unittest.TestCase):
    extractor = java.Extractor()

    def test_constant(self):
        im, compiled = compile_annotated_expr("nat", "42")
        expr = shims.expr_from_ivy(im, compiled)
        extracted = Naive(80).format(self.extractor.visit_expr(expr))
        self.assertEqual(extracted.layout(), "42")

    def test_app(self):
        expr = terms.Apply(None,
                           "lengthy_addition_function_oh_no",
                           [terms.Constant(None, "41"), terms.Constant(None, "1")])

        extracted = Naive(80).format(self.extractor.visit_expr(expr))
        self.assertEqual(extracted.layout(), "lengthy_addition_function_oh_no(41, 1)")

    def test_binop(self):
        large_num = str(10000000000000);
        expr = terms.BinOp(None,
                           terms.Constant(None, large_num),
                           "+",
                           terms.Constant(None, large_num))

        extracted = Naive(80).format(self.extractor.visit_expr(expr))
        self.assertEqual(extracted.layout(), large_num + " + " + large_num)

    def test_ite(self):
        test = terms.BinOp(None,
                           terms.Constant(None, "1"),
                           "<",
                           terms.Constant(None, "2"))
        then = terms.Constant(None, "f")
        els = terms.Constant(None, "g")
        expr = terms.Ite(None, test, then, els)

        extracted = Naive(80).format(self.extractor.visit_expr(expr))
        self.assertEqual(extracted.layout(), "1 < 2 ? f : g")

    def test_unop(self):
        # Trivial expressions can have parens elided.
        expr = terms.UnOp(None, "!", terms.Constant(None, "true"))
        extracted = Naive(80).format(self.extractor.visit_expr(expr))
        self.assertEqual(extracted.layout(), "!true")

        # Non-simple expressions should be wrapped in parens.
        test = terms.BinOp(None,
                           terms.Constant(None, "1"),
                           "<",
                           terms.Constant(None, "2"))
        expr = terms.UnOp(None, "-", test)

        extracted = Naive(80).format(self.extractor.visit_expr(expr))
        self.assertEqual(extracted.layout(), "-(1 < 2)")

    def test_if(self):
        test = terms.BinOp(None, terms.Constant(None, "1"), "<", terms.Constant(None, "2"))
        then = terms.Call(None, terms.Apply(None, "f", []))
        els = None
        stmt = terms.If(None, test, then, els)

        extracted = self.extractor.visit_action(stmt)
        layout = Naive(80).format(extracted).layout()
        self.assertEqual(layout, "\n".join([
            "if (1 < 2) {",
            "  f();",
            "}"
        ]))

    def test_if_else(self):
        test = terms.BinOp(None, terms.Constant(None, "1"), "<", terms.Constant(None, "2"))
        then = terms.Call(None, terms.Apply(None, "f", []))
        els = terms.Call(None, terms.Apply(None, "g", []))
        stmt = terms.If(None, test, then, els)

        extracted = self.extractor.visit_action(stmt)
        layout = Naive(80).format(extracted).layout()
        self.assertEqual(layout, "\n".join([
            "if (1 < 2) {",
            "  f();",
            "} else {",
            "  g();",
            "}"
        ]))

    def test_let_single_binding(self):
        stmt = terms.Let(None,
                         [Binding("x", "nat")],
                         terms.Assign(None, terms.Constant(None, "x"), terms.Constant(None, "42")))
        extracted = self.extractor.visit_action(stmt)
        layout = Naive(80).format(extracted).layout()
        self.assertEqual(layout, "\n".join([
            "int x;",
            "x = 42;"
        ]))

    def test_let_multi_binding(self):
        stmt = terms.Let(None,
                         [Binding("x", "int"),
                          Binding("y", "bool")],
                         terms.Sequence(None, [
                             terms.Assign(None, terms.Constant(None, "x"), terms.Constant(None, "42")),
                             terms.Assign(None, terms.Constant(None, "y"), terms.Constant(None, "true"))]))
        extracted = self.extractor.visit_action(stmt)
        layout = Naive(80).format(extracted).layout()
        self.assertEqual(layout, "\n".join([
            "int x;",
            "bool y;",
            "x = 42;",
            "y = true;",
        ]))
