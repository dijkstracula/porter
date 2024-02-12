from porter.pp import Doc, Text, Line, Nest, Nil, utils

semi = Text(";")

soft_open_bracket = Text("{") + utils.soft_line
soft_close_bracket = utils.soft_line + Text("}")


def block(contents: Doc) -> Doc:
    return Text("{") + Line() + Nest(4, contents) + Line() + Text("}")


def quoted(contents: Doc | str) -> Doc:
    if isinstance(contents, str):
        contents = Text(contents)
    return Text('"') + contents + Text('"')


def canonicalize_identifier(s: str) -> str:
    return s \
        .replace(".", "__") \
        .replace("fml:", "") \
        .replace(":", "__") \
        .replace("[", "_of_") \
        .replace("]", "_")
