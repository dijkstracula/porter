import os
import pathlib

import pytest
import warnings

from . import compile_ivy
import porter.ivy as pivy
from porter.ivy import extensionality, shims
from porter.ast import terms
from porter.extraction import java
from porter.pp.formatter import Naive

progdir = os.path.join(os.path.dirname(__file__), 'programs')


def compile_and_parse(fn) -> terms.Program:
    oldcwd = os.getcwd()
    os.chdir(os.path.dirname(fn))
    with open(fn) as f:
        im, ag = compile_ivy(f)
    os.chdir(oldcwd)
    return shims.program_from_ivy(im)


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
def test_compile_and_extract(fn):
    prog = compile_and_parse(fn)

    extractor = java.Extractor()
    formatted = Naive(80).format(extractor.extract(prog))
    _layout = formatted.layout()
    pass


@pytest.mark.parametrize("fn", glob_progs('ivy-ts', 'src'))
def test_ivy_ts(fn: pathlib.Path):
    compile_and_parse(fn)


@pytest.mark.parametrize("fn", glob_progs('accord-ivy', 'src'))
def test_accord(fn: pathlib.Path):
    compile_and_parse(fn)
