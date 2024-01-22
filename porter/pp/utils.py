from . import *

from typing import Union

# TODO: I hate calling this util.

space = Text(" ")
soft_line = space | Line()
comma_sep = Text(", ") | Line()


def sep(d1: Doc, d2: Doc, op: Union[Doc, str] = " "):
    if isinstance(op, str):
        op = Text(op)
    return d1 + op + d2


def dotted(d1: Doc, d2: Doc):
    return sep(d1, d2, ".")


def enclosed(opened: str, d: Union[Doc, str], closed: str):
    if isinstance(d, str):
        d = Text(d)
    soft_open = Text(opened) + soft_line  # "{ " or "{\n"
    soft_closed = soft_line + Text(closed)  # " }" or "\n}"
    return soft_open + d + soft_closed


class BlockScope:
    indent: int

    def __init__(self, indent=2):
        self.indent = indent

    def curly_wrapped(self, d: Doc) -> Doc:
        return enclosed("{", Nest(self.indent, d), "}")
