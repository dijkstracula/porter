from dataclasses import dataclass

from ivy import ivy_utils as iu

from typing import Any, Optional

from . import Binding, Position

from .sorts import Sort


@dataclass
class AST:
    pos: Position



@dataclass
class ActionDefinition:
    formal_params: list[Binding[Sort]]
    formal_returns: list[Binding[Sort]]
    body: list[Any]  # TODO


#
class Expr:
    pass


#


@dataclass
class Record:
    fields: list[Binding[Sort]]
    actions: list[Binding[ActionDefinition]]


#

@dataclass
class Stmt:
    pass


@dataclass
class Assert(Stmt):
    pred: Expr


@dataclass
class Assume(Stmt):
    pred: Expr
