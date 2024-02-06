import os
import pathlib

import pytest
import warnings

from . import progdir
from porter.ivy import shims
from porter.ast import terms
from porter.extraction import java
from porter.pp.formatter import Naive

from pathlib import Path


def compile_and_parse(fn) -> terms.Program:
    return shims.handle_isolate(Path(fn))


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
    prog = shims.handle_isolate(Path(fn))

    formatted = Naive(80).format(java.extract(os.path.basename(fn), prog))
    _layout = formatted.layout()
    pass


@pytest.mark.parametrize("fn", glob_progs('ivy-ts', 'src'))
def test_ivy_ts(fn: str):
    _prog = shims.handle_isolate(Path(fn))


@pytest.mark.parametrize("fn", glob_progs('accord-ivy', 'src'))
def test_accord_subfiles(fn: str):
    prog = shims.handle_isolate(Path(fn))
    formatted = Naive(80).format(java.extract(os.path.basename(fn), prog))
    _layout = formatted.layout()


@pytest.mark.parametrize("fn", glob_progs('accord-ivy', 'src'))
def test_accord_subfiles(fn: str):
    prog = shims.handle_isolate(Path(fn))
    formatted = Naive(80).format(java.extract(os.path.basename(fn), prog))
    _layout = formatted.layout()


def test_accord():
    fn = os.path.join(progdir, 'accord-ivy', 'src', 'protocol.ivy')
    prog = shims.handle_isolate(Path(fn))
    formatted = Naive(80).format(java.extract(os.path.basename(fn), prog))
    _layout = formatted.layout()
