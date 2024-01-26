from . import *

from typing import Union

# TODO: I hate calling this util.

space = Text(" ")
soft_line = space | Line()
soft_comma = Text(",") + soft_line


def join(ds: list[Doc], op: Union[Doc, str] = " "):
    if len(ds) == 0:
        return Nil()
    if len(ds) == 1:
        return ds[0]
    if isinstance(op, str):
        op = Text(op)
    return ds[0] + op + join(ds[1:], op)


def padded(op: Union[Doc, str]):
    if isinstance(op, str):
        op = Text(op)
    return soft_line + op + soft_line


def dotted(d1: Doc, d2: Doc):
    return join([d1, d2], ".")


def enclosed(opened: str, d: Union[Doc, str], closed: str):
    if isinstance(d, str):
        d = Text(d)

    single_line = Text(opened) + d + Text(closed)
    multi_line = Text(opened) + Line() + Nest(2, d) + Line() + Text(closed)
    return single_line | multi_line


class BlockScope:
    indent: int

    def __init__(self, indent=2):
        self.indent = indent

    def curly_wrapped(self, d: Doc) -> Doc:
        return enclosed("{", Nest(self.indent, d), "}")
