from . import *


class BlockScope:
    indent: int

    def __init__(self, indent=2):
        self.indent = indent

    def curly_wrapped(self, d: Doc) -> Doc:
        return Text("{") + Line(self.indent, d) + Text("}")
