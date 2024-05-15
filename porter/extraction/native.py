from porter.ast import terms
from porter.ast.terms.visitor import MutVisitor

from typing import Tuple

def native_sort_converter(as_ivy: str) -> str:
    """This is a wildly-annoying hack: for cases where we are extracting a generic
    Java type from native code, we only have the string representation of the _ivy_
    sort, not a Sort AST node.  So, in essence, we have to parse the string into
    a Java type.  Hopefully there are not too many cases where this has to happen."""
    match as_ivy:
        case "uint[8]": return "Byte"
        case sort: return sort

# TODO: Will also need one for NativeTypes.
class NativeRewriter(MutVisitor):
    natives: dict[Tuple[str, int], str]

    def __init__(self, natives: dict[Tuple[str, int], str]):
        self.natives = natives

    def _finish_native_action(self, act: terms.NativeAct, args: list[None]):
        pos = act.pos()
        if pos is None:
            # Not annotated with an Ivy source location, so nothing we can expect to do...
            # TODO: warn
            return
        loc = pos.filename, pos.line
        replacement_fmt = self.natives.get(loc)

        if replacement_fmt:
            act.fmt = replacement_fmt
