from dataclasses import dataclass

from typing import Optional

from ivy import logic as ilog
from ivy import ivy_module as imod


# Sorts

@dataclass
class Sort:
    pass


@dataclass
class Uninterpreted(Sort):
    name: str


@dataclass
class Bool(Sort):
    pass


@dataclass
class Numeric(Sort):
    lo_range: Optional[int]
    hi_range: Optional[int]

    @staticmethod
    def int_sort():
        return Numeric(None, None)

    @staticmethod
    def nat_sort():
        return Numeric(0, None)


@dataclass
class BitVec(Sort):
    width: int


@dataclass
class Enumeration(Sort):
    discriminants: list[str]


@dataclass
class Function(Sort):
    domain: list[Sort]
    range: Sort


def from_ivy(sort) -> Sort:
    if hasattr(sort, "name"):
        name = sort.name
        if name == "bool":
            return Bool()
        if name == "int":
            return Numeric.int_sort()
        if name == "nat":
            return Numeric.nat_sort()
        if isinstance(sort, ilog.UninterpretedSort):
            return Uninterpreted(name)
    if hasattr(sort, "sort"):
        return from_ivy(sort.sort)
    if isinstance(sort, ilog.EnumeratedSort):
        discriminants = [str(x) for x in sort.extension]
        return Enumeration(discriminants)
    if isinstance(sort, ilog.FunctionSort):
        domain = [from_ivy(s) for s in sort.domain]
        ret = from_ivy(sort.range)
        return Function(domain, ret)
    raise Exception(f"TODO {type(sort)}")
