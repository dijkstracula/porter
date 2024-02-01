from porter.ivy import extensionality, shims
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


def test_extensionality_visitor():
    prog = compile_and_parse(os.path.join(progdir, "004_relations_and_invariants.ivy"))
    ext = extensionality.NonExtensionals(None)
    ext.visit_program(prog)

    # `link` has a logical assignment `link(x, Y) := false`, so by the
    # ivy_to_cpp rules it is not extensional.
    assert("link" in ext.nons)

    # The remaining relations do not violate the ivy_to_cpp rules so
    # we should not have expected to accumulate them during visiting.
    assert("semaphore" not in ext.nons)
    assert("conn_counts" not in ext.nons)
    pass
