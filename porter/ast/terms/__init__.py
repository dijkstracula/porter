from dataclasses import dataclass
from enum import Enum

from typing import Any, Optional, TypeVar

from porter.ast import AST, Binding

from porter.ast.sorts import Sort

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
class Var(Expr):
    rep: str


@dataclass
class BinOp(Expr):
    lhs: Expr
    op: str
    rhs: Expr


@dataclass
class Apply(Expr):
    # TODO: should this instead be called Atom?
    relsym: str
    args: list[Expr]


@dataclass
class Ite(Expr):
    test: Expr
    then: Expr
    els: Expr


@dataclass
class Exists(Expr):
    vars: list[Binding[Sort]]
    expr: Expr


@dataclass
class Forall(Expr):
    vars: list[Binding[Sort]]
    expr: Expr


#

SomeStrategy = Enum("SomeStrategy", ["ARBITRARY", "MINIMISE", "MAXIMISE"])


@dataclass
class Some(Expr):
    # TODO: I would like to rename this node.
    vars: list[Binding[Sort]]
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
class LogicalAssign(Action):
    vars: list[Var]
    assign: Assign

    @staticmethod
    def maybe_from_assign(a: Assign) -> Optional["LogicalAssign"]:
        """ If the given assignment involves an application involving a logical variable, lift it into
        its corresponding LogicalAssignment."""
        match a.lhs:
            case Apply(ivy, _relsym, args):
                lvars = [a for a in args if isinstance(a, Var)]
                if len(lvars) > 0:
                    return LogicalAssign(ivy, lvars, a)
        return None


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
    vardecls: list[Binding[Sort]]
    scope: Action


@dataclass
class Native(Action):
    lang: str
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
class FunctionDefinition(AST):
    formal_params: list[Binding[Sort]]
    body: Expr


@dataclass
class ActionDefinition(AST):
    kind: ActionKind
    formal_params: list[Binding[Sort]]
    # XXX: At the moment I do not handle multiple returns.  In theory
    # we should be able to just lift them into a Tuple at extraction
    # time, but for the moment things will Just Blow Up, Probably.
    formal_returns: list[Binding[Sort]]
    body: Action


@dataclass
class Record(AST):
    fields: list[Binding[Sort]]
    actions: list[Binding[ActionDefinition]]


#

@dataclass
class Program(AST):
    sorts: list[Binding[Sort]]

    individuals: list[Binding[Sort]]
    inits: list[Action]

    actions: list[Binding[ActionDefinition]]
    functions: list[Binding[FunctionDefinition]]

    conjectures: list[Binding[Expr]]
