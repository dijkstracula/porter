from porter.ast import terms
from porter.ast.terms.visitor import MutVisitor

from typing import Tuple


# TODO: Will also need one for NativeTypes.
class NativeRewriter(MutVisitor):
    natives: dict[Tuple[str, int], str]

    def __init__(self, natives: dict[Tuple[str, int], str]):
        self.natives = natives

    def _finish_native(self, act: terms.Native, args: list[None]):
        pos = act.pos()
        if pos is None:
            # Not annotated with an Ivy source location, so nothing we can expect to do...
            # TODO: warn
            return
        loc = pos.filename, pos.line
        replacement_fmt = self.natives.get(loc)

        if replacement_fmt:
            act.fmt = replacement_fmt
