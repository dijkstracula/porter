from porter.pp import *
from porter.pp.formatter import Naive
from porter.pp.utils import enclosed

import unittest


class PrettyASTTests(unittest.TestCase):
    def test_enclosed(self):
        # str arg
        wrapped = enclosed("{ ", "a := b", " }").flatten()
        self.assertEqual(wrapped.layout(), "{ a := b }")

        # Doc arg
        wrapped = enclosed("{ ", Text("a := b"), " }").flatten()
        self.assertEqual(wrapped.layout(), "{ a := b }")

    def test_block_flatten(self):
        ast = Text("if 1 < 2") + Text(" ") + enclosed("{ ", "a := b", " }")
        flattened = ast.flatten()
        self.assertEqual(flattened.layout(), "if 1 < 2 { a := b }")

    def test_naive_formatter(self):
        ast = Text("if 1 < 2") + Text(" ") + enclosed("{ ", "some_lengthy_lhs_var := some_complicated_rhs_var", " }")

        # Here, we have plenty of room.
        canonical = Naive(120).format(ast)
        self.assertEqual(canonical.layout(), "if 1 < 2 { some_lengthy_lhs_var := some_complicated_rhs_var }")

        # Here, we have hardly any room.
        canonical = Naive(10).format(ast)
        self.assertEqual(canonical.layout(), "if 1 < 2 { \n    some_lengthy_lhs_var := some_complicated_rhs_var\n }")
