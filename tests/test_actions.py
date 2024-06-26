from ivy import ivy_actions as iact
from ivy import ivy_module as imod

import porter.ast
from . import compile_toplevel, extract_after_init
from typing import Tuple

from porter.ast import sorts, terms

from porter.ivy.shims import action_def_from_ivy, action_from_ivy, PARAM_PREFIX

import unittest


def compile_action(name: str, action: str) -> Tuple[imod.Module, iact.Action]:
    exported = "export " + action
    (im, _) = compile_toplevel(exported)

    action_ast = im.actions["ext:" + name]
    assert isinstance(action_ast, iact.Action)
    return im, action_ast


class ActionTest(unittest.TestCase):

    def test_inc_action(self):
        action = "action inc(n: nat) returns (m: nat) = { m := n + 1 }"
        im, compiled = compile_action("inc", action)
        act = action_def_from_ivy(im, "inc", compiled)
        self.assertEqual(act.formal_params, [porter.ast.Binding(PARAM_PREFIX + "fml:n", sorts.Number.nat_sort())])
        self.assertEqual(act.formal_returns, [porter.ast.Binding("fml:m", sorts.Number.nat_sort())])

        # Body should be shaped like Let(fml:n, Sequence{ fml:n := porter_param:fml:n; fml:m := n + 1 })
        body = act.body

        # Even though a nat is pass by value anyway, we copy it into a mutable local.
        assert isinstance(body, terms.Let)
        self.assertEqual(body.vardecls, [porter.ast.Binding("fml:n", sorts.Number.nat_sort())])

        # The body of the let has two actions: one copies the param into the temporary and the other assigns to the ret
        body = body.scope
        assert isinstance(body, terms.Sequence)
        assert len(body.stmts) == 2

        stmt = body.stmts[0]
        assert isinstance(stmt, terms.Assign)
        assert isinstance(stmt.lhs, terms.Constant)
        assert isinstance(stmt.rhs, terms.Constant)

        stmt = body.stmts[1]
        assert isinstance(stmt, terms.Assign)
        assert isinstance(stmt.lhs, terms.Constant)
        self.assertTrue(stmt.rhs.op, "+")
        assert isinstance(stmt.rhs, terms.BinOp)

    def test_while_with_decreases(self):
        action = """action id(n: nat) returns (m: nat) = {
                     m := 0;
                     while n > 0 
                        decreases n
                     { 
                        m := m + 1; 
                        n := n - 1;
                     }
                 }"""
        im, compiled = compile_action("id", action)
        assert isinstance(compiled, iact.Sequence)
        assert isinstance(compiled.args[0], iact.AssignAction)  # m := 0
        assert isinstance(compiled.args[1], iact.WhileAction)  # while [test] [body] [ranking]

        while_ast = action_from_ivy(im, compiled.args[1])
        assert isinstance(while_ast, terms.While)

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
        assert isinstance(act.stmts[0], terms.Assign)
        assert isinstance(act.stmts[1], terms.Let)

    def test_apply_multi_arg(self):
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
        assert isinstance(act.stmts[0], terms.Assign)
        assert isinstance(act.stmts[1], terms.Let)

    def test_logical_assign_lift(self):
        from porter.ast import sorts

        action = terms.Assign(None,
                              terms.Apply(None, "f", [terms.Constant(None, "x")]),
                              terms.Constant(None, "false"))
        self.assertIsNone(terms.LogicalAssign.maybe_from_assign(action))

        action = terms.Assign(None,
                              terms.Apply(None, "f", [terms.Var(None, "X")]),
                              terms.Constant(None, "false"))
        laction = terms.LogicalAssign.maybe_from_assign(action)
        self.assertIsNotNone(laction)
        assert isinstance(laction, terms.LogicalAssign)
        self.assertEqual(laction.vars, [terms.Var(None, "X")])
