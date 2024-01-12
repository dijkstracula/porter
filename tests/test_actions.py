from ivy import ivy_actions as iact
from ivy import ivy_module as imod
from ivy import logic as ilog

import porter.ast
from . import compile_toplevel, extract_after_init
from typing import Any, Tuple

from porter.ast import terms, sorts

from porter.ivy_shim import action_def_from_ivy

import unittest


class ExprTest(unittest.TestCase):
    def compile_action(self, name: str, action: str) -> Tuple[imod.Module, iact.Action]:
        exported = "export " + action
        (im, _) = compile_toplevel(exported)

        action_ast = im.actions["ext:" + name]
        assert isinstance(action_ast, iact.Action)
        return im, action_ast

    def test_inc_action(self):
        action = "action inc(n: nat) returns (m: nat) = { m := n + 1 }"
        im, compiled = self.compile_action("inc", action)
        expr = action_def_from_ivy(im, compiled)
        self.assertEqual(expr.formal_params, [porter.ast.Binding("n", sorts.Numeric.nat_sort())])
        self.assertEqual(expr.formal_returns, [porter.ast.Binding("m", sorts.Numeric.nat_sort())])
        self.assertEqual(len(expr.body), 1)

        pass

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
        pass