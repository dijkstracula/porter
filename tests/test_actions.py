from ivy import ivy_actions as iact
from ivy import ivy_module as imod
from ivy import logic as ilog

import porter.ast
from . import compile_toplevel, extract_after_init
from typing import Any, Tuple

from porter.ast import terms, sorts

from porter.ivy_shim import action_def_from_ivy, action_from_ivy

import unittest


def compile_action(name: str, action: str) -> Tuple[imod.Module, iact.Action]:
    exported = "export " + action
    (im, _) = compile_toplevel(exported)

    action_ast = im.actions["ext:" + name]
    assert isinstance(action_ast, iact.Action)
    return im, action_ast


class ExprTest(unittest.TestCase):

    def test_inc_action(self):
        action = "action inc(n: nat) returns (m: nat) = { m := n + 1 }"
        im, compiled = compile_action("inc", action)
        act = action_def_from_ivy(im, "inc", compiled)
        self.assertEqual(act.formal_params, [porter.ast.Binding("n", sorts.Numeric.nat_sort())])
        self.assertEqual(act.formal_returns, [porter.ast.Binding("m", sorts.Numeric.nat_sort())])

        body = act.body
        assert isinstance(body, terms.Assign)
        assert isinstance(body.lhs, terms.Constant)
        assert isinstance(body.rhs, terms.BinOp)
        self.assertTrue(body.rhs.op, "+")

    def test_apply_action(self):
        action = "action inc(n: nat) returns (m: nat) = { m := n + 1 }"
        init_act = "after init { " \
                   f"""var test_expr: nat := inc(41);
                    var ensure_no_dead_code_elim: nat := test_expr;
                    test_expr := ensure_no_dead_code_elim;
                }}"""
        im, compiled = compile_toplevel("\n".join([action, init_act]))
        test_expr_assign = extract_after_init(im)

        # NB: from Ivy To CPP: "tricky: a call can have variables on the lhs. we lower this to
        # a call with temporary return actual followed by assignment"
        assert isinstance(test_expr_assign, iact.Sequence)
        self.assertEqual(len(test_expr_assign.args), 2)
        assert isinstance(test_expr_assign.args[0], iact.CallAction)
        assert isinstance(test_expr_assign.args[1], iact.LocalAction)

        # "var test_expr: nat := inc(41)" is a sequence of two parts: binding the return value to the temporary
        # and then assigning the temporary to test_expr.
        act = action_from_ivy(im, test_expr_assign)
        assert isinstance(act, terms.Sequence)
        assert isinstance(act.stmts[0], terms.Let)
        assert isinstance(act.stmts[1], terms.Let)

    def test_apply_action_multi_arg(self):
        action = "action addition(m:nat, n: nat) returns (p: nat) = { p := m + n }"
        init_act = "after init { " \
                   f"""var test_expr: nat := addition(41, 1);
                    var ensure_no_dead_code_elim: nat := test_expr;
                    test_expr := ensure_no_dead_code_elim;
                }}"""
        im, compiled = compile_toplevel("\n".join([action, init_act]))
        test_expr_assign = extract_after_init(im)

        # NB: from Ivy To CPP: "tricky: a call can have variables on the lhs. we lower this to
        # a call with temporary return actual followed by assignment"
        assert isinstance(test_expr_assign, iact.Sequence)
        self.assertEqual(len(test_expr_assign.args), 2)
        assert isinstance(test_expr_assign.args[0], iact.CallAction)
        assert isinstance(test_expr_assign.args[1], iact.LocalAction)

        # "var test_expr: nat := inc(41)" is a sequence of two parts: binding the return value to the temporary
        # and then assigning the temporary to test_expr.
        act = action_from_ivy(im, test_expr_assign)
        assert isinstance(act, terms.Sequence)
        assert isinstance(act.stmts[0], terms.Let)
        assert isinstance(act.stmts[1], terms.Let)
