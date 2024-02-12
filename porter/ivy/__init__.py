from ivy import ivy_logic as ilog
from ivy import logic as log
from ivy import ivy_module as imod
from ivy import ivy_utils as iu

from dataclasses import dataclass

from pathlib import Path
from typing import Iterable, Optional


@dataclass
class Position:
    filename: Path
    line: int
    reference: Optional["Position"]

    @staticmethod
    def from_ivy(ivy_pos: iu.LocationTuple) -> "Position":
        if len(ivy_pos) > 2:
            assert (isinstance(ivy_pos.reference, iu.LocationTuple))
            if isinstance(ivy_pos.filename, Path):
                fn = ivy_pos.filename
            elif isinstance(ivy_pos.filename, str):
                fn = Path(ivy_pos.filename)
            else:
                raise Exception(f"What kind of data is ivy_pos.filename? It is a f{type(ivy_pos.reference)}")

            return Position(ivy_pos.filename or "<stdin>", ivy_pos.line, Position.from_ivy(ivy_pos.reference))
        else:
            return Position(ivy_pos.filename or "<stdin>", ivy_pos.line, None)


def symbols(im: imod.Module) -> Iterable[log.Const]:
    memo = set()
    for name, sym in im.sig.symbols.items():
        if name in ["<", "<=", "=", ">", ">="]:
            continue  # XXX: disgusting hack for now
        if isinstance(sym, ilog.UnionSort):
            for sym in sym.sorts:
                assert isinstance(sym, log.Const)
                if sym not in memo:
                    memo.add(sym)
                    yield sym
        elif isinstance(sym, log.Const):
            if sym not in memo:
                memo.add(sym)
                yield sym
        else:
            raise Exception(f"symbols: TODO: {name} = {sym}")


def sort_has_domain(sort) -> bool:
    if not hasattr(sort, "dom"):
        return False
    return len(sort.dom) > 0


def members(im: imod.Module) -> Iterable[log.Const]:
    defns = set([d.formula.defines().name for d in im.definitions + im.native_definitions])
    for sym in symbols(im):
        if sym.name in im.destructor_sorts:
            continue
        if sym.name in defns:
            continue
        yield sym


def state_symbols(im: imod.Module) -> Iterable[log.Const]:
    for sym in symbols(im):
        if sym not in im.sig.constructors and sym in im.sig.interp:
            yield sym


def individuals(im: imod.Module) -> Iterable[log.Const]:
    for sym in symbols(im):
        if not sort_has_domain(sym.sort):
            yield sym
