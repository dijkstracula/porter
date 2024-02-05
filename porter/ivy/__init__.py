from ivy import ivy_logic as ilog
from ivy import logic as log
from ivy import ivy_module as imod

from typing import Iterable

from ..passes import extensionality


def symbols(im: imod.Module) -> Iterable[log.Const]:
    memo = set()
    for name, sym in im.sig.symbols.items():
        if name in ["<", "<=", "=", ">", ">="]:
            continue  # XXX: disgusting hack for now
        if isinstance(sym, ilog.UnionSort):
            for sym in sym.sort.sorts:
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


def members(im: imod.Module) -> Iterable[log.Const]:
    for sym in symbols(im):
        if sym.name not in im.destructor_sorts:
            yield sym


def state_symbols(im: imod.Module) -> Iterable[log.Const]:
    for sym in symbols(im):
        if sym not in im.sig.constructors and sym in im.sig.interp:
            yield sym


def individuals(im: imod.Module) -> Iterable[log.Const]:
    for sym in symbols(im):
        if not extensionality.sort_has_domain(sym.sort):
            yield sym
