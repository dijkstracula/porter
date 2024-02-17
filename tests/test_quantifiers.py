from porter.ast import Binding, sorts, terms
from porter.passes.quantifiers import BoundExprs, Polarity
from porter.quantifiers.bounds import NumericInterval, interval_from_sort_uses

import unittest


class SortRangeTests(unittest.TestCase):

    def test_bounded_uninterpreted(self):
        sort = sorts.Uninterpreted("foo")
        bound = 42
        q = NumericInterval.from_sort(sort)
        self.assertEqual(q.constrain_upper(bound), NumericInterval(None, bound))
        self.assertEqual(q.constrain_lower(bound), NumericInterval(bound, None))

    def test_bounded_numerics(self):
        nat = sorts.Number.nat_sort()
        bound = 42
        q = NumericInterval.from_sort(nat)
        self.assertEqual(q.constrain_upper(bound), NumericInterval(0, bound))
        self.assertEqual(q.constrain_lower(bound), NumericInterval(42, None))

    def test_sort_ranges_single(self):
        X = Binding("X", sorts.Number.int_sort())
        x_lt_ten = terms.BinOp(None, terms.Var(None, "X"), "<", terms.Constant(None, "10"))
        bounds = [(X, x_lt_ten)]
        self.assertEqual(interval_from_sort_uses(bounds), [Binding("X", NumericInterval(None, 9))])

    def test_sort_ranges_multiple(self):
        X = Binding("X", sorts.Number.int_sort())
        zero_le_x = terms.BinOp(None, terms.Constant(None, "0"), "<=", terms.Var(None, "X"))
        x_lt_ten = terms.BinOp(None, terms.Var(None, "X"), "<", terms.Constant(None, "10"))
        bounds = [(X, zero_le_x), (X, x_lt_ten)]
        self.assertEqual(interval_from_sort_uses(bounds), [Binding("X", NumericInterval(0, 9))])


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

        self.assertEqual(bound_exprs, [(X, zero_ge_x), (X, x_le_10)])

    def test_disjunction_exprs(self):
        X = Binding("X", sorts.Number.nat_sort())
        zero_ge_x = terms.BinOp(None, terms.Constant(None, "0"), ">=", terms.Var(None, "X"))
        x_le_10 = terms.BinOp(None, terms.Var(None, "X"), "<=", terms.Constant(None, "10"))
        fmla = terms.Forall(None,
                            [X],
                            terms.BinOp(None, zero_ge_x, "or", x_le_10))
        bound_exprs = BoundExprs.from_forall(fmla)

        self.assertEqual(bound_exprs, [(X, zero_ge_x), (X, x_le_10)])

        fmla = terms.Exists(None,
                            [Binding("X", sorts.Number.nat_sort())],
                            terms.BinOp(None, zero_ge_x, "or", x_le_10))
        bound_exprs = BoundExprs.from_exists(fmla)
        self.assertEqual(bound_exprs, [])
