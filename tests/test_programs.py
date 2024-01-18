import os
import pathlib

import pytest
import warnings

from . import compile_ivy
from porter import ivy_shim
from porter.ast import toplevels

progdir = os.path.join(os.path.dirname(__file__), 'programs')


def compile_and_parse(fn) -> toplevels.Program:
    oldcwd = os.getcwd()
    os.chdir(os.path.dirname(fn))
    with open(fn) as f:
        im, ag = compile_ivy(f)
        return ivy_shim.program_from_ivy(im)
    os.chdir(oldcwd)


def glob_progs(*paths):
    src_dir = os.path.join(progdir, *paths)
    if not os.path.exists(src_dir):
        warnings.warn(f"{src_dir} not found (did you clone with --recurse-submodules?)")
        return
    for fn in os.listdir(src_dir):
        fn = os.path.join(src_dir, fn)
        yield fn


unit_tests = [os.path.join(progdir, f) for f in os.listdir(progdir) if os.path.isfile(os.path.join(progdir, f))]


@pytest.mark.parametrize("fn", unit_tests)
def test_isolate(fn):
    compile_and_parse(fn)


@pytest.mark.parametrize("fn", glob_progs('ivy-ts', 'src'))
def test_ivy_ts(fn: pathlib.Path):
    compile_and_parse(fn)


@pytest.mark.parametrize("fn", glob_progs('accord-ivy', 'src'))
def test_accord(fn: pathlib.Path):
    compile_and_parse(fn)
