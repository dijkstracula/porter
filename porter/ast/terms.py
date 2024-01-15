from dataclasses import dataclass, field

from ivy import ivy_utils as iu

from typing import Any, Generic, Optional, TypeVar

from . import Binding, Position

from . import sorts
from .sorts import Sort


@dataclass
class AST:
    _ivy_node: Optional[Any] = field(repr=False)

    def pos(self) -> Optional[Position]:
        if self._ivy_node is None:
            return None
        if not hasattr(self._ivy_node, 'lineno'):
            return None
        if not isinstance(self._ivy_node.lineno, iu.LocationTuple):
            raise Exception(f"What is a lineno?  It's a {type(self._ivy_node.lineno)} as opposed to an iu.LocationTuple")
        return Position.from_ivy(self._ivy_node.lineno)

    def sort(self) -> Optional[Sort]:
        if self._ivy_node is None:
            return None
        if not hasattr(self._ivy_node, 'sort'):
            raise Exception(f"Missing sort for {self._ivy_node}")
        return sorts.from_ivy(self._ivy_node)


#
class Expr(AST):
    # TODO: what should the relationship between an Expr and a Formula be?
    pass


@dataclass
class Constant(Expr):
    rep: str


@dataclass
class BinOp(Expr):
    lhs: Expr
    op: Any
    rhs: Expr


@dataclass
class Apply(Expr):
    # TODO: should this instead be called Atom?
    relsym: Constant
    args: list[Expr]


#


@dataclass
class Record(AST):
    fields: list[Binding[Sort]]
    actions: list[Binding["ActionDefinition"]]


#

@dataclass
class Action(AST):
    pass


@dataclass
class Assert(Action):
    pred: Expr


@dataclass
class Assume(Action):
    pred: Expr


@dataclass
class Call(Action):
    app: Apply


@dataclass
class Ensures(Action):
    pred: Expr


@dataclass
class Requires(Action):
    pred: Expr


@dataclass
class Assign(Action):
    lhs: Expr
    rhs: Expr


@dataclass
class Sequence(Action):
    stmts: list[Action]


@dataclass
class If(Action):
    test: Expr
    then: Action
    els: Optional[Action]


@dataclass
class While(Action):
    test: Expr
    do: Action


@dataclass
class Let(Action):
    vardecls: list[Binding[Sort]]
    scope: Action


@dataclass
class ActionDefinition(AST):
    formal_params: list[Binding[Sort]]
    formal_returns: list[Binding[Sort]]
    body: Action
