from porter.ast import Binding, sorts, terms
from porter.ivy.shims import program_from_ivy
from porter.passes.quantifiers import BoundExprs, Polarity
from porter.quantifiers.bounds import AppIteration, NumericInterval, constraints_from_exprs

import unittest

from tests import compile_toplevel


class SortRangeTests(unittest.TestCase):

    def test_bounded_uninterpreted(self):
        sort = sorts.Uninterpreted("foo")
        bound = 42
        q = NumericInterval.from_binding(Binding("some_val", sort))
        self.assertEqual(q.constrain_upper(bound), NumericInterval("some_val", None, bound))
        self.assertEqual(q.constrain_lower(bound), NumericInterval("some_val", bound, None))

    def test_bounded_numerics(self):
        nat = sorts.Number.nat_sort()
        bound = 42
        q = NumericInterval.from_binding(Binding("some_nat", nat))
        self.assertEqual(q.constrain_upper(bound), NumericInterval("some_nat", 0, bound))
        self.assertEqual(q.constrain_lower(bound), NumericInterval("some_nat", 42, None))

    def test_sort_ranges_single(self):
        X = Binding("X", sorts.Number.int_sort())
        x_lt_ten = terms.BinOp(None, terms.Var(None, "X"), "<", terms.Constant(None, "10"))
        bounds = [(X, x_lt_ten)]
        self.assertEqual(constraints_from_exprs(bounds), [NumericInterval("X", None, 9)])

    def test_sort_ranges_multiple(self):
        X = Binding("X", sorts.Number.int_sort())
        zero_le_x = terms.BinOp(None, terms.Constant(None, "0"), "<=", terms.Var(None, "X"))
        x_lt_ten = terms.BinOp(None, terms.Var(None, "X"), "<", terms.Constant(None, "10"))
        bounds = [(X, zero_le_x), (X, x_lt_ten)]
        self.assertEqual(constraints_from_exprs(bounds), [NumericInterval("X", 0, None), NumericInterval("X", None, 9)])

    def test_apply_exprs_name_matches(self):
        X = Binding("X", sorts.Number.nat_sort())
        app = terms.Apply(None, "foo", [terms.Var(None, X.name)])
        cstrs = constraints_from_exprs([(X, app)])

        self.assertEqual(cstrs, [AppIteration("X", app, [terms.Var(None, X.name)])])

    def test_apply_exprs_name_differs(self):
        X = Binding("X", sorts.Number.nat_sort())
        Y = Binding("Y", sorts.Number.nat_sort())
        app = terms.Apply(None, "foo", [terms.Var(None, X.name)])
        cstrs = constraints_from_exprs([(Y, app)])

        self.assertEqual(cstrs, [AppIteration("Y", app, [None])])


class BoundExprsTests(unittest.TestCase):
    def test_simple_fmla(self):
        fmla = terms.Forall(None, [Binding("X", sorts.Number.nat_sort())],
                            terms.BinOp(None, terms.Var(None, "X"), "<=", terms.Var(None, "X")))

        bound_exprs = BoundExprs("X", Polarity.Forall).visit_expr(fmla.expr)
        assert bound_exprs == [fmla.expr]

    def test_conjunction_exprs(self):
        X = Binding("X", sorts.Number.nat_sort())
        zero_ge_x = terms.BinOp(None, terms.Constant(None, "0"), ">=", terms.Var(None, "X"))
        x_le_10 = terms.BinOp(None, terms.Var(None, "X"), "<=", terms.Constant(None, "10"))
        fmla = terms.Forall(None,
                            [Binding("X", sorts.Number.nat_sort())],
                            terms.BinOp(None, zero_ge_x, "and", x_le_10))
        bound_exprs = BoundExprs.from_forall(fmla)
        self.assertEqual(bound_exprs, [])

        fmla = terms.Exists(None,
                            [X],
                            terms.BinOp(None, zero_ge_x, "and", x_le_10))
        bound_exprs = BoundExprs.from_exists(fmla)

        x_le_zero = terms.BinOp(None, terms.Var(None, "X"), "<=", terms.Constant(None, "0"))
        self.assertEqual(bound_exprs, [(X, x_le_zero), (X, x_le_10)])

    def test_disjunction_exprs(self):
        X = Binding("X", sorts.Number.nat_sort())
        zero_ge_x = terms.BinOp(None, terms.Constant(None, "0"), ">=", terms.Var(None, "X"))
        x_le_10 = terms.BinOp(None, terms.Var(None, "X"), "<=", terms.Constant(None, "10"))
        fmla = terms.Forall(None,
                            [X],
                            terms.BinOp(None, zero_ge_x, "or", x_le_10))
        bound_exprs = BoundExprs.from_forall(fmla)

        x_le_zero = terms.BinOp(None, terms.Var(None, "X"), "<=", terms.Constant(None, "0"))
        self.assertEqual(bound_exprs, [(X, x_le_zero), (X, x_le_10)])

        fmla = terms.Exists(None,
                            [Binding("X", sorts.Number.nat_sort())],
                            terms.BinOp(None, zero_ge_x, "or", x_le_10))
        bound_exprs = BoundExprs.from_exists(fmla)
        self.assertEqual(bound_exprs, [])

    def test_member_existential(self):
        mod = """
        include collections
        include numbers
        include order

        module set(basis) = {
            type this

            instance arridx : unbounded_sequence
            instance arr:array(arridx,basis)

            destructor repr(X:this) : arr.t

            relation member(E:basis,S:this)
            definition member(y: basis, X:this) =
              exists Z : arridx.
                0 <= Z & Z < repr(X).end & repr(X).value(Z) = y

            action emptyset returns(s:this)
            implement emptyset {
                repr(s) := arr.create(0,0)
            }

            after emptyset {
                assert ~member(E,s);
            }
        }

        type node_id = {0..3}
        instantiate nodeset : set(node_id)

        var s : nodeset

        after init {
            s := nodeset.emptyset;
        } 
        """
        im, _ = compile_toplevel(mod)
        prog = program_from_ivy(im)
        pass #TODO
