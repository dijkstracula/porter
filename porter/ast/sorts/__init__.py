from ivy import ivy_ast as iast
from ivy import logic as ilog

from dataclasses import dataclass
from typing import Optional

# Sorts

SortName = str


@dataclass(frozen=True)
class Sort:
    pass


@dataclass(frozen=True)
class Uninterpreted(Sort):
    sort_name: str


@dataclass(frozen=True)
class Bool(Sort):
    pass


@dataclass(frozen=True)
class Native(Sort):
    lang: str
    fmt: str  # TODO: in Ivy this is a NativeCode
    args: list  # TODO: of what?


@dataclass(frozen=True)
class Number(Sort):
    sort_name: str
    lo_range: Optional[int]
    hi_range: Optional[int]

    @staticmethod
    def int_sort():
        return Number("int", None, None)

    @staticmethod
    def nat_sort():
        return Number("nat", 0, None)

    def name(self):
        return self.sort_name


@dataclass(frozen=True)
class BitVec(Sort):
    width: int


@dataclass(frozen=True)
class Enumeration(Sort):
    sort_name: str
    discriminants: tuple[str, ...]


@dataclass(frozen=True)
class Function(Sort):
    domain: list[Sort]
    range: Sort


def from_ivy(sort) -> Sort:
    if hasattr(sort, "name"):
        name = sort.name
        if name == "bool":
            return Bool()
        if name == "int":
            return Number.int_sort()
        if name == "nat":
            return Number.nat_sort()
        if isinstance(sort, ilog.UninterpretedSort):
            return Uninterpreted(name)
        if isinstance(sort, ilog.EnumeratedSort):
            discriminants = tuple([str(x) for x in sort.extension])
            return Enumeration(name, discriminants)
    if hasattr(sort, "sort"):
        return from_ivy(sort.sort)
    if isinstance(sort, ilog.FunctionSort):
        domain = [from_ivy(s) for s in sort.domain]
        ret = from_ivy(sort.range)
        return Function(domain, ret)
    if isinstance(sort, iast.NativeType):
        native_code = sort.args[0]
        assert isinstance(native_code, iast.NativeCode)
        native_blob = native_code.code
        args = [str(arg) for arg in sort.args[1:]]
        return Native("c++", native_blob, args)
    raise Exception(f"TODO {type(sort)}")
