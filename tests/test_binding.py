from ivy import logic as ilog
from ivy import ivy_module as imod

from porter import ast, ivy_shim

import unittest


class BindingTests(unittest.TestCase):
    def test_ivy_const_to_binding(self):
        c = ilog.Const("prm:V0", ilog.UninterpretedSort("nat"))
        with imod.Module() as im:
            sort = ivy_shim.binding_from_ivy_const(im, c)
            self.assertEqual(sort, ast.Binding("prm:V0", ast.NumericSort.nat_sort()))
