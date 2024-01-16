import os
import pytest
import unittest

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