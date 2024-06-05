from porter.pp import Doc, Text, Line, Nest, Nil, utils

from typing import Optional

SCALA_RESERVED_WORDS = {"abstract", "case", "catch", "class", "def", "do", "else", "extends", "final",
                        "finally", "for", "forSome", "if", "implicit", "import", "lazy", "macro", "match", "new",
                        "null", "object", "override", "package", "private", "protected", "return", "sealed", "super",
                        "this", "throw", "trait", "try", "type", "val", "var", "while", "with", "yield"}


def lift(x: Doc | str) -> Doc:
    if isinstance(x, str):
        x = Text(x)
    return x


def block(contents: Doc) -> Doc:
    return Text("{") + Line() + Nest(4, contents) + Line() + Text("}")


def quoted(contents: Doc | str) -> Doc:
    return Text('"') + lift(contents) + Text('"')


def commented(contents: Text | str) -> Doc:
    return Text("// ") + lift(contents) + Line()


def arglist(params: list[Doc]) -> Doc:
    if len(params) == 0:
        return Nil()
    return utils.enclosed("(", utils.join(params), ")")


def typelist(params: Doc | list[Doc]) -> Doc:
    if isinstance(params, list):
        return utils.enclosed("[", utils.join(params), "]")
    return utils.enclosed("[", params, "]")


def canonicalize_identifier(s: str) -> str:
    global SCALA_RESERVED_WORDS
    s = s \
        .replace(".", "__") \
        .replace("fml:", "") \
        .replace(":", "__") \
        .replace("[", "_of_") \
        .replace("]", "_")
    if s in SCALA_RESERVED_WORDS:
        return f"{s}_ident"
    return s


##

def assign(lhs: Doc | str, rhs: Doc | str):
    return lift(lhs) + utils.padded("=") + lift(rhs) + Line()


def binop(lhs: Doc | str, op: Doc | str, rhs: Doc | str):
    return lift(lhs) + utils.soft_line + lift(op) + utils.soft_line + lift(rhs)


def func_sig(name: Doc | str, params: list[Doc], ret: Optional[Doc | str]):
    sig = Text("def ") + lift(name) + arglist(params)
    if ret:
        sig += Text(": ") + lift(ret)
    return sig


def local_decl(name: Doc | str, sort: Optional[Doc | str], init: Optional[Doc | str], mutable=False):
    doc = (Text("var ") if mutable else Text("val ")) + lift(name)
    if sort is not None:
        doc += Text(": ") + lift(sort)
    if init is not None:
        doc = doc + utils.padded("=") + lift(init)
    return doc + Line()
