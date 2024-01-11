from dataclasses import dataclass, field

from ivy import ivy_utils as iu

from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class Binding(Generic[T]):
    name: str
    decl: T


class Position:
    filename: str
    line: int
    reference: Optional["Position"]

    @staticmethod
    def from_ivy(ivy_pos: iu.LocationTuple) -> "Position":
        Position(ivy_pos[0], ivy_pos[1], ivy_pos.get(2))


@dataclass
class AST:
    pos: Position


# Sorts

@dataclass
class Sort:
    pass


@dataclass
class UninterpretedSort(Sort):
    name: str


@dataclass
class BoolSort(Sort):
    pass


@dataclass
class NumericSort(Sort):
    lo_range: Optional[int]
    hi_range: Optional[int]

    @staticmethod
    def int_sort():
        return NumericSort(None, None)

    @staticmethod
    def nat_sort():
        return NumericSort(0, None)


@dataclass
class BitVecSort(Sort):
    width: int


@dataclass
class EnumSort(Sort):
    discriminants: list[str]


@dataclass
class FunctionSort(Sort):
    domain: list[Sort]
    range: Sort


@dataclass
class ActionDefinition:
    formal_params: list[Binding[Sort]]
    formal_returns: list[Binding[Sort]]
    body: list[Any]  # TODO


@dataclass
class Record:
    fields: list[Binding[Sort]]
    actions: list[Binding[ActionDefinition]]
