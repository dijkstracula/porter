from porter.ivy import shims
from porter.passes import quantifiers, freevars, native_rewriter
from porter.ast import terms
import os

from . import compile_ivy, progdir


def compile_and_parse(fn) -> terms.Program:
    oldcwd = os.getcwd()
    os.chdir(os.path.dirname(fn))
    with open(fn) as f:
        im, ag = compile_ivy(f)
    os.chdir(oldcwd)
    return shims.program_from_ivy(im)


def test_extensionality_pass():
    prog = compile_and_parse(os.path.join(progdir, "004_relations_and_invariants.ivy"))
    ext = quantifiers.NonExtensionals(None)
    ext.visit_program(prog)

    # conn_counts, link, and semaphore should be in prog.individuals.

    # `link` has a logical assignment `link(x, Y) := false`, so by the
    # ivy_to_cpp rules it is not extensional.
    assert ("link" in ext.nons)

    # The remaining relations do not violate the ivy_to_cpp rules so
    # we should not have expected to accumulate them during visiting.
    assert ("semaphore" not in ext.nons)
    assert ("conn_counts" not in ext.nons)


def test_freevar_pass():
    prog = compile_and_parse(os.path.join(progdir, "004_relations_and_invariants.ivy"))

    assert(prog.conjectures[0].name == "unique_conn") # just so we confirm we know which invariant we're dealing with.
    fvs = freevars.FreeVars()
    fvs.visit_expr(prog.conjectures[0].decl)
    assert(fvs.vars == set(["X", "Y", "Z"]))

    # This invariant doesn't implicitly use free variables but explicitly quantifies
    # over them, so we should get the empty set here.
    assert(prog.conjectures[1].name == "connect_downs_sem")
    fvs = freevars.FreeVars()
    fvs.visit_expr(prog.conjectures[1].decl)
    assert(fvs.vars == set([]))


def test_native_rewriter():
    prog = compile_and_parse(os.path.join(progdir, "006_pingpong.ivy"))
    native_rewriter.visit(prog)
