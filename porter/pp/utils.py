from . import *

from typing import Union

space = Text(" ")
soft_line = space | Line()
soft_comma = Text(",") + soft_line


def join(ds: list[Doc], op: Union[Doc, str] = soft_comma):
    if len(ds) == 0:
        return Nil()
    if len(ds) == 1:
        return ds[0]
    if isinstance(ds[0], Nil):
        return join(ds[1:], op)

    if isinstance(op, str):
        op = Text(op)
    return ds[0] + op + join(ds[1:], op)


def padded(op: Union[Doc, str]):
    if isinstance(op, str):
        op = Text(op)
    return space + op + space


def dotted(d1: Doc, d2: Doc):
    return join([d1, d2], ".")


def enclosed(opened: str, d: Union[Doc, str], closed: str, hardnl=False):
    if isinstance(d, str):
        d = Text(d)

    single_line = Text(opened) + d + Text(closed)
    multi_line = Text(opened) + Line() + Nest(4, d) + Line() + Text(closed)
    if not hardnl:
        return single_line | multi_line
    else:
        return multi_line
