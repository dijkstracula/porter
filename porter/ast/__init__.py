from dataclasses import dataclass, field, KW_ONLY

from porter.ivy import Position

from ivy import ivy_actions as iact
from ivy import ivy_utils as iu

from porter.ast import sorts

from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class Binding(Generic[T]):
    name: str
    decl: T


@dataclass()
class AST:
    _ivy_node: Optional[Any] = field(repr=False)
    _sort: Optional[sorts.Sort] = field(init=False, repr=False)

    def __post_init__(self):
        if self._ivy_node is None:
            self._sort = None
        elif isinstance(self._ivy_node, iact.Action):
            # TODO: contemplate a top sort
            self._sort = None
        elif not hasattr(self._ivy_node, 'sort'):
            # raise Exception(f"Missing sort for {self._ivy_node}")
            self._sort = None
        else:
            self._sort = sorts.from_ivy(self._ivy_node)

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
        return self._sort

    @property
    def ivy_node(self):
        return self._ivy_node

