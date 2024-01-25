from dataclasses import dataclass
from enum import Enum

from typing import Any, Optional, TypeVar

from porter.ast import AST, Binding

from porter.ast.sorts import Sort, SortName

T = TypeVar("T")


#
class Expr(AST):
    # TODO: what should the relationship between an Expr and a Formula be?
    # At the present they're the same.  That's probably fine?
    pass


@dataclass
class Constant(Expr):
    rep: str


@dataclass
class BinOp(Expr):
    lhs: Expr
    op: str
    rhs: Expr


@dataclass
class Apply(Expr):
    # TODO: should this instead be called Atom?
    relsym: Expr
    args: list[Expr]


@dataclass
class Ite(Expr):
    test: Expr
    then: Expr
    els: Expr


@dataclass
class Exists(Expr):
    vars: list[Binding[SortName]]
    expr: Expr


@dataclass
class Forall(Expr):
    vars: list[Binding[SortName]]
    expr: Expr


#

SomeStrategy = Enum("SomeStrategy", ["ARBITRARY", "MINIMISE", "MAXIMISE"])


@dataclass
class Some(Expr):
    # TODO: I would like to rename this node.
    vars: list[Binding[SortName]]
    fmla: Expr
    strat: SomeStrategy


@dataclass
class UnOp(Expr):
    op: Any
    expr: Expr


#


@dataclass
class Action(AST):
    pass


@dataclass
class Assert(Action):
    pred: Expr


@dataclass
class Assign(Action):
    lhs: Expr
    rhs: Expr


@dataclass
class Assume(Action):
    pred: Expr


@dataclass
class Call(Action):
    app: Apply


@dataclass
class Debug(Action):
    msg: str
    args: list[Binding[Expr]]


@dataclass
class Ensures(Action):
    pred: Expr


@dataclass
class Havok(Action):
    modifies: list[Expr]


@dataclass
class If(Action):
    test: Expr
    then: Action
    els: Optional[Action]


@dataclass
class Let(Action):
    vardecls: list[Binding[SortName]]
    scope: Action


@dataclass
class Native(Action):
    fmt: str  # TODO: in Ivy this is a NativeCode
    args: list[Expr]


@dataclass
class Requires(Action):
    pred: Expr


@dataclass
class Sequence(Action):
    stmts: list[Action]


@dataclass
class While(Action):
    test: Expr
    decreases: Optional[Expr]
    do: Action


ActionKind = Enum("ActionKind", ["NORMAL", "EXPORTED", "IMPORTED"])


@dataclass
class ActionDefinition(AST):
    kind: ActionKind
    formal_params: list[Binding[SortName]]
    formal_returns: list[Binding[SortName]]
    body: Action


@dataclass
class Record(AST):
    fields: list[Binding[SortName]]
    actions: list[Binding[ActionDefinition]]


#

@dataclass
class Program(AST):
    sorts: list[Sort]
    individuals: list[Binding[SortName]]
    inits: list[Action]
    actions: list[Binding[ActionDefinition]]
