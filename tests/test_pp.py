from porter.pp import *
from porter.pp.utils import enclosed, BlockScope

import unittest


class PrettyASTTest(unittest.TestCase):
    pass


class BlockScopeTest(unittest.TestCase):
    def test_enclosed(self):
        # str arg
        wrapped = enclosed("{", "a := b", "}").flatten()
        self.assertEqual(wrapped.layout(), "{ a := b }")

        # Doc arg
        wrapped = enclosed("{", Text("a := b"), "}").flatten()
        self.assertEqual(wrapped.layout(), "{ a := b }")

    def test_block_flatten(self):
        cond = Text("if 1 < 2")
        body = enclosed("{", "a := b", "}").flatten()
        ast = cond + Text(" ") + body
        flattened = ast.flatten()
        self.assertEqual(flattened.layout(), "if 1 < 2 { a := b }")
