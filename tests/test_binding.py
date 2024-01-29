import unittest

from ivy import logic as ilog

from porter.ivy import shims
from porter.ast import Binding


class BindingTests(unittest.TestCase):
    def test_ivy_const_to_binding(self):
        c = ilog.Const("prm:V0", ilog.UninterpretedSort("nat"))
        sort = shims.binding_from_ivy_const(c)
        self.assertEqual(sort, Binding("prm:V0", "nat"))
