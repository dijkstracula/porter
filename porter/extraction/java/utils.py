from porter.pp import Doc, Text, Line, Nest, utils

semi = Text(";")
soft_open_bracket = Text("{") + utils.soft_line
soft_close_bracket = utils.soft_line + Text("}")

SCALA_RESERVED_WORDS = {"abstract", "case", "catch", "class", "def", "do", "else", "extends", "final",
                        "finally", "for", "forSome", "if", "implicit", "import", "lazy", "macro", "match", "new",
                        "null", "object", "override", "package", "private", "protected", "return", "sealed", "super",
                        "this", "throw", "trait", "try", "type", "val", "var", "while", "with", "yield"}


def block(contents: Doc) -> Doc:
    return Text("{") + Line() + Nest(4, contents) + Line() + Text("}")


def quoted(contents: Doc | str) -> Doc:
    if isinstance(contents, str):
        contents = Text(contents)
    return Text('"') + contents + Text('"')


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


def record_metaclass_name(name: str):
    return name + "__ivysort"
