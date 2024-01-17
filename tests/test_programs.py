import os
import pathlib

import pytest
import warnings

from . import compile_ivy
from porter import ivy_shim

progdir = os.path.join(os.path.dirname(__file__), 'programs')
tests = [f for f in os.listdir(progdir) if os.path.isfile(os.path.join(progdir, f))]


@pytest.mark.parametrize("fn", tests)
def test_prog(fn):
    fn = os.path.join(progdir, fn)
    with open(fn) as f:
        im, ag = compile_ivy(f)
        prog = ivy_shim.program_from_ivy(im)
        pass


def glob_progs(*paths):
    src_dir = os.path.join(progdir, *paths)
    if not os.path.exists(src_dir):
        warnings.warn(f"{src_dir} not found (did you clone with --recurse-submodules?)")
        return
    for fn in os.listdir(src_dir):
        fn = os.path.join(src_dir, fn)
        yield fn


@pytest.mark.parametrize("fn", glob_progs('ivy-ts', 'src'))
def test_ivy_ts(fn: pathlib.Path):
    oldcwd = os.getcwd()
    os.chdir(os.path.dirname(fn))
    test_prog(fn)
    os.chdir(oldcwd)