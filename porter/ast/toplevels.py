from enum import Enum
from dataclasses import dataclass

from . import AST, Binding
from .sorts import Sort
from .terms import Action

ActionKind = Enum("ActionKind", ["NORMAL", "EXPORTED", "IMPORTED"])


@dataclass
class ActionDefinition(AST):
    kind: ActionKind
    formal_params: list[Binding[Sort]]
    formal_returns: list[Binding[Sort]]
    body: Action


@dataclass
class Program(AST):
    sorts: list[Sort]
    individuals: list[Binding[Sort]]
    inits: list[Action]
    actions: list[Binding[ActionDefinition]]
