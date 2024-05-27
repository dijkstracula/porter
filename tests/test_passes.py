from porter.ivy import shims
from porter.quantifiers.extensionality import NonExtensionals
from porter.passes import logic_vars, native_rewriter
from porter.ast import terms, sorts
import os

from . import compile_ivy, progdir

import unittest


def compile_and_parse(fn) -> terms.Program:
    oldcwd = os.getcwd()
    os.chdir(os.path.dirname(fn))
    with open(fn) as f:
        im, ag = compile_ivy(f)
    os.chdir(oldcwd)
    return shims.program_from_ivy(im)


class FreevarPasses(unittest.TestCase):
    def test_freevar_pass(self):
        prog = compile_and_parse(os.path.join(progdir, "004_relations_and_invariants.ivy"))

        self.assertEqual(prog.conjectures[0].name,
                         "symmetric_link")  # just so we confirm we know which invariant we're dealing with.
        fvs = logic_vars.FreeVars()
        fvs.visit_expr(prog.conjectures[0].decl)
        self.assertEqual(fvs.vars, set(["X", "Y"]))

        # This invariant doesn't implicitly use free variables but explicitly quantifies
        # over them, so we should get the empty set here.
        self.assertEqual(prog.conjectures[1].name, "symmetric_link_explicit")
        fvs = logic_vars.FreeVars()
        fvs.visit_expr(prog.conjectures[1].decl)
        self.assertEqual(fvs.vars, set([]))

    def test_bindvar_binop(self):
        expr = terms.BinOp(None, terms.Constant(None, "0"), "<=", terms.Var(None, "X"))
        bound = logic_vars.BindVar("X").visit_expr(expr)
        self.assertEqual(bound,
                         terms.BinOp(None, terms.Constant(None, "0"), "<=", terms.Constant(None, "X")))

    def test_bindvar_apply(self):
        expr = terms.Apply(None, "foo", [
            terms.Var(None, "X"),
            terms.Var(None, "Y"),
        ])

        bound = logic_vars.BindVar("X").visit_expr(expr)
        self.assertEqual(bound,
                         terms.Apply(None, "foo", [
                             terms.Constant(None, "X"),
                             terms.Var(None, "Y"),
                         ]))


def test_native_rewriter():
    prog = compile_and_parse(os.path.join(progdir, "006_pingpong.ivy"))
    native_rewriter.visit(prog)
