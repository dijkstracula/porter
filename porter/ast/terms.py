from dataclasses import dataclass

from ivy import ivy_utils as iu

from typing import Any, Generic, Optional, TypeVar

from . import Binding, Position

from . import sorts
from .sorts import Sort


@dataclass
class AST:
    ivy_node: Optional[Any]

    def pos(self) -> Optional[Position]:
        if self.ivy_node is None:
            return None
        if not hasattr(self.ivy_node, 'lineno'):
            return None
        if not isinstance(self.ivy_node.lineno, iu.LocationTuple):
            raise Exception(f"What is a lineno?  It's a {type(self.ivy_node.lineno)} as opposed to an iu.LocationTuple")
        return Position.from_ivy(self.ivy_node.lineno)

    def sort(self) -> Optional[Sort]:
        if self.ivy_node is None:
            return None
        if not hasattr(self.ivy_node, 'sort'):
            raise Exception(f"Missing sort for {self.ivy_node}")
        return sorts.from_ivy(self.ivy_node)


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
    relsym: str
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
    pass



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
    body: list[Action]
