from dataclasses import dataclass, field

from ivy import ivy_utils as iu

from porter.ast import sorts

from typing import Any, Generic, Optional, TypeVar

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


@dataclass
class AST:
    _ivy_node: Optional[Any] = field(repr=False)

    def pos(self) -> Optional[Position]:
        if self._ivy_node is None:
            return None
        if not hasattr(self._ivy_node, 'lineno'):
            return None
        if not isinstance(self._ivy_node.lineno, iu.LocationTuple):
            raise Exception(
                f"What is a lineno?  It's a {type(self._ivy_node.lineno)} as opposed to an iu.LocationTuple")
        return Position.from_ivy(self._ivy_node.lineno)

    def sort(self) -> Optional[sorts.Sort]:
        if self._ivy_node is None:
            return None
        if not hasattr(self._ivy_node, 'sort'):
            raise Exception(f"Missing sort for {self._ivy_node}")
        return sorts.from_ivy(self._ivy_node)
