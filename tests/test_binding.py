import unittest

from ivy import ivy_module as imod
from ivy import logic as ilog

from porter import ivy_shim
from porter.ast import Binding, sorts


class BindingTests(unittest.TestCase):
    def test_ivy_const_to_binding(self):
        c = ilog.Const("prm:V0", ilog.UninterpretedSort("nat"))
        sort = ivy_shim.binding_from_ivy_const(c)
        self.assertEqual(sort, Binding("prm:V0", sorts.Number.nat_sort()))
