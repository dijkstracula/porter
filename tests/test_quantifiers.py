from porter.ast import Binding, sorts, terms

from porter.passes import quantifiers

import unittest


class SortRangeTests(unittest.TestCase):
    def test_bounded_uninterpreted(self):
        sort = sorts.Uninterpreted("foo")
        bound = 42
        q = quantifiers.NumericInterval.from_sort(sort)
        self.assertEquals(q.constrain_upper(bound), quantifiers.NumericInterval(None, bound))
        self.assertEquals(q.constrain_lower(bound), quantifiers.NumericInterval(bound, None))

    def test_bounded_numerics(self):
        nat = sorts.Number.nat_sort()
        bound = 42
        q = quantifiers.NumericInterval.from_sort(nat)
        self.assertEquals(q.constrain_upper(bound), quantifiers.NumericInterval(0, bound))
        self.assertEquals(q.constrain_lower(bound), quantifiers.NumericInterval(42, None))

    def test_sort_ranges_single(self):
        X = Binding("X", sorts.Number.int_sort())
        x_lt_ten = terms.BinOp(None, terms.Var(None, "X"), "<", terms.Constant(None, "10"))
        bounds = [(X, x_lt_ten)]
        self.assertEquals(quantifiers.interval_from_binops(bounds), [Binding("X", quantifiers.NumericInterval(None, 9))])

    def test_sort_ranges_multiple(self):
        X = Binding("X", sorts.Number.int_sort())
        zero_le_x = terms.BinOp(None, terms.Constant(None, "0"), "<=", terms.Var(None, "X"))
        x_lt_ten = terms.BinOp(None, terms.Var(None, "X"), "<", terms.Constant(None, "10"))
        bounds = [(X, zero_le_x), (X, x_lt_ten)]
        self.assertEquals(quantifiers.interval_from_binops(bounds), [Binding("X", quantifiers.NumericInterval(0, 9))])


class BoundExprsTests(unittest.TestCase):
    def test_simple_fmla(self):
        fmla = terms.Forall(None, [Binding("X", sorts.Number.nat_sort())],
                            terms.BinOp(None, terms.Var(None, "X"), "<=", terms.Var(None, "X")))

        bound_exprs = quantifiers.BoundExprs("X", quantifiers.Polarity.Forall).visit_expr(fmla.expr)
        assert bound_exprs == [fmla.expr]

    def test_conjunction_bounds(self):
        X = Binding("X", sorts.Number.nat_sort())
        zero_ge_x = terms.BinOp(None, terms.Constant(None, "0"), ">=", terms.Var(None, "X"))
        x_le_10 = terms.BinOp(None, terms.Var(None, "X"), "<=", terms.Constant(None, "10"))
        fmla = terms.Forall(None,
                            [Binding("X", sorts.Number.nat_sort())],
                            terms.BinOp(None, zero_ge_x, "&", x_le_10))
        bound_exprs = quantifiers.BoundExprs.from_forall(fmla)
        self.assertEquals(bound_exprs, [])

        fmla = terms.Exists(None,
                            [X],
                            terms.BinOp(None, zero_ge_x, "&", x_le_10))
        bound_exprs = quantifiers.BoundExprs.from_exists(fmla)

        x_le_0 = terms.BinOp(None, terms.Var(None, "X"), "<=", terms.Constant(None, "0"))
        self.assertEquals(bound_exprs, [(X, x_le_0), (X, x_le_10)])

    def test_disjunction_bounds(self):
        X = Binding("X", sorts.Number.nat_sort())
        zero_ge_x = terms.BinOp(None, terms.Constant(None, "0"), ">=", terms.Var(None, "X"))
        x_le_10 = terms.BinOp(None, terms.Var(None, "X"), "<=", terms.Constant(None, "10"))
        fmla = terms.Forall(None,
                            [X],
                            terms.BinOp(None, zero_ge_x, "|", x_le_10))
        bound_exprs = quantifiers.BoundExprs.from_forall(fmla)

        zero_le_x = terms.BinOp(None, terms.Var(None, "X"), "<=", terms.Constant(None, "0"))
        self.assertEquals(bound_exprs, [(X, zero_le_x), (X, x_le_10)])

        fmla = terms.Exists(None,
                            [Binding("X", sorts.Number.nat_sort())],
                            terms.BinOp(None, zero_ge_x, "|", x_le_10))
        bound_exprs = quantifiers.BoundExprs.from_exists(fmla)
        self.assertEquals(bound_exprs, [])
