from ivy import logic as ilog
from ivy import ivy_module as imod

from porter import ast, ivy_shim
from porter.ast import terms, sorts

from . import compile_toplevel

import unittest


class RecordTest(unittest.TestCase):
    def test_strip_prefix(self):
        self.assertEqual(ivy_shim.strip_prefixes([], ".", "a.b.c"), "a.b.c")
        self.assertEqual(ivy_shim.strip_prefixes(["b"], ".", "a.b.c"), "a.b.c")
        self.assertEqual(ivy_shim.strip_prefixes(["a"], ".", "a.b.c"), "b.c")
        self.assertEqual(ivy_shim.strip_prefixes(["a", "b"], ".", "a.b.c"), "c")
        self.assertEqual(ivy_shim.strip_prefixes(["a", "z"], ".", "a.b.c"), "a.b.c")

    def test_record_conversion(self):
        cls = """class foo = { 
                field x: nat
                field y: nat
                action sum(self: foo) returns (z: nat) = {
                  z := self.x + self.y 
                }
              }
              after init {
                var f: foo;
                f.x := f.x;
                var z := f.sum();
              }"""
        (im, ag) = compile_toplevel(cls)

        # Ensure the module is well-formed
        self.assertIn("foo", im.sort_constructors.keys())
        self.assertIn("foo", im.sort_destructors.keys())
        fields = im.sort_destructors["foo"]
        self.assertTrue(fields[0].name == "foo.x")
        self.assertTrue(fields[1].name == "foo.y")

        rec = ivy_shim.record_from_ivy(im, "foo")
        assert isinstance(rec, terms.Record)

        # Fields
        self.assertEqual(len(rec.fields), 2)
        self.assertEqual(rec.fields[0], ast.Binding("x", sorts.Numeric.nat_sort()))
        self.assertEqual(rec.fields[1], ast.Binding("y", sorts.Numeric.nat_sort()))

        # Actions
        self.assertEqual(len(rec.actions), 1)
        self.assertTrue(rec.actions[0].name, "sum")
        self.assertEqual(type(rec.actions[0].decl), terms.ActionDefinition)
        self.assertTrue(type(rec.actions[0].decl.formal_params[0].name), "self")
        self.assertTrue(type(rec.actions[0].decl.formal_returns[0].name), "z")
        pass