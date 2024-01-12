from dataclasses import dataclass

from ivy import ivy_utils as iu

from typing import Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class Binding(Generic[T]):
    name: str
    decl: T


@dataclass
class Position:
    filename: str
    line: int
    reference: Optional["Position"]

    @staticmethod
    def from_ivy(ivy_pos: iu.LocationTuple) -> "Position":
        return Position(ivy_pos[0] or "<stdin>", ivy_pos[1], ivy_pos.get(2))
