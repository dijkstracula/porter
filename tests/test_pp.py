from porter.pp import *
from porter.pp.formatter import naive
from porter.pp.utils import enclosed

import unittest


class PrettyASTTest(unittest.TestCase):
    def test_enclosed(self):
        # str arg
        wrapped = enclosed("{", "a := b", "}").flatten()
        self.assertEqual(wrapped.layout(), "{ a := b }")

        # Doc arg
        wrapped = enclosed("{", Text("a := b"), "}").flatten()
        self.assertEqual(wrapped.layout(), "{ a := b }")

    def test_block_flatten(self):
        ast = Text("if 1 < 2") + Text(" ") + enclosed("{", "a := b", "}")
        flattened = ast.flatten()
        self.assertEqual(flattened.layout(), "if 1 < 2 { a := b }")

    def test_naive_formatter(self):
        ast = Text("if 1 < 2") + Text(" ") + enclosed("{", "some_lengthy_lhs_var := some_complicated_rhs_var", "}")

        # Here, we have plenty of room.
        canonical = naive(80, 0, ast)
        self.assertEqual(canonical.layout(), "if 1 < 2 { some_lengthy_lhs_var := some_complicated_rhs_var }")

        # Here, we have hardly any room.
        canonical = naive(80, 70, ast)
        self.assertEqual(canonical.layout(), "if 1 < 2 {\nsome_lengthy_lhs_var := some_complicated_rhs_var\n}")

        # Here, we have some room, and an awkward concequence of the naive formatter: because we greedily determine
        # if a pp tree can fit, we do not newline the opening brace but _do_ newline the closing one, which looks weird.
        canonical = naive(80, 30, ast)
        self.assertEqual(canonical.layout(), "if 1 < 2 { some_lengthy_lhs_var := some_complicated_rhs_var\n}")
