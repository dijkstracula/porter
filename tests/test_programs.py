import os
import pytest
import unittest

from . import compile_ivy

progdir = os.path.join(os.path.dirname(__file__), 'programs')
tests = [os.path.join(progdir, f) for f in os.listdir(progdir) if os.path.isfile(os.path.join(progdir, f))]


@pytest.mark.parametrize("fn", tests)
def test_program_parse(fn):
    with open(fn) as f:
        im, ag = compile_ivy(f)
