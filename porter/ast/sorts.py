from dataclasses import dataclass

from typing import Optional


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
class Enum(Sort):
    discriminants: list[str]


@dataclass
class Function(Sort):
    domain: list[Sort]
    range: Sort
