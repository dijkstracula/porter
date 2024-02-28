import os

import pytest
import warnings

from . import progdir
from porter.ivy import shims
from porter.ast import sorts, terms
from porter.extraction import java
from porter.pp import Doc
from porter.pp.formatter import Naive

from pathlib import Path

import unittest


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


@pytest.mark.parametrize("fn", glob_progs('accord-ivy', 'src'))
def test_accord_subfiles(fn: str):
    prog = shims.handle_isolate(Path(fn))
    formatted = Naive(80).format(java.extract(os.path.basename(fn), prog))
    _layout = formatted.layout()


@pytest.mark.parametrize("fn", glob_progs('ivy-ts', 'src'))
def test_ivy_ts_subfiles(fn: str):
    prog = shims.handle_isolate(Path(fn))
    formatted = Naive(80).format(java.extract(os.path.basename(fn), prog))
    _layout = formatted.layout()


def test_accord():
    fn = os.path.join(progdir, 'accord-ivy', 'src', 'protocol.ivy')
    prog = shims.handle_isolate(Path(fn))
    formatted = Naive(80).format(java.extract(os.path.basename(fn), prog))
    _layout = formatted.layout()


class ShimTests(unittest.TestCase):
    """ A bunch of specific things we want to check on a particular non-trivial Ivy program."""

    prog: terms.Program
    formatted: Doc
    layout: str

    def setUp(self) -> None:
        fn = os.path.join(progdir, '006_pingpong.ivy')
        self.prog = shims.handle_isolate(Path(fn))
        self.formatted = Naive(80).format(java.extract(os.path.basename(fn), self.prog))
        self.layout = self.formatted.layout()

    def test_interpreted_from_sig(self):
        # im.sig.interp has some interpretations of uninterpreted sorts.  Make sure we
        # slurp those up correctly.
        self.assertIn("pid", self.prog.sorts)
        self.assertEqual(self.prog.sorts["pid"], sorts.Number("pid", 0, 1))

    def test_class_field_extraction(self):
        # Ping-Pong accesses fields in a class like so:
        #         if msg.typ = ping_kind {
        #             msg.typ := pong_kind;
        #             msg.dst := msg.src;
        #             msg.src := self;
        #             sock.send(proc(msg.dst).sock.id, msg);
        #         } else {
        #
        # The AST we get back from Ivy representes the LHS of these accesses
        # as unary relations, so we have to do some irritating mangling at extraction
        # time.
        self.assertIn("msg.dst = msg.src", self.layout)
