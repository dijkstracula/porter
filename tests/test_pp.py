from porter.pp import *
from porter.pp.block_scoped import BlockScope

import unittest


class PrettyASTTest(unittest.TestCase):
    pass


class BlockScopeTest(unittest.TestCase):
    def test_curly_wrapped(self):
        bs = BlockScope(2)
        ast = Text("a := 42;")
        wrapped = bs.curly_wrapped(ast)
        self.assertEqual(
            wrapped,
            Text("{") + Line(2, ast) + Text("}")
        )

    def test_block_flatten(self):
        cond = Text("if 1 < 2")
        body = Text("{") + Line(2, Text("a := 42;")) + Text("}")
        ast = cond + Text(" ") + body
        _flattened = ast.flatten()
