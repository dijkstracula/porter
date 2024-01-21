""" The world's most naive pretty-printing combinators, after
Wadler (https://homepages.inf.ed.ac.uk/wadler/papers/prettier/prettier.pdf). """

from dataclasses import dataclass, field


class Doc:
    def pretty(self, width: int):
        raise NotImplementedError

    def __add__(self, other: "Doc") -> "Doc":
        "Sugar for horizontal concatenation."
        return Concat(self, other)

    def __or__(self, other: "Doc") -> "Doc":
        "Sugar for choice."
        return Union(self, other)

    def group(self) -> "Doc":
        """Produces the layout of the doc, where the layouts may be
        compressed onto a single line."""
        match self:
            case Nil():
                return Nil()
            case Concat(lhs, rhs):
                return lhs.group() + rhs.group()
            case Text(s):
                return Text(s)
            case Line(i, x):
                return (Text(" ") + x.flatten()) | Line(i, x)
            case Union(d1, d2):
                d1.group() | d2.group()

    def flatten(self) -> "Doc":
        """Replaces all line breaks with a single space."""
        match self:
            case Nil():
                return Nil()
            case Concat(lhs, rhs):
                return Concat(lhs.flatten(), rhs.flatten())
            case Text(s):
                return Text(s)
            case Line(_, x):
                return Text(" ") + x.flatten()
            case Union(d1, _):
                return d1.flatten()


@dataclass
class Nil(Doc):
    "The unit value of a document - one with no text to format."
    pass


@dataclass
class Concat(Doc):
    "The horizontal concatenation of two documents: Wadler's :<> datatype."
    lhs: Doc
    rhs: Doc


@dataclass
class Text(Doc):
    "A text literal."
    text: str


@dataclass
class Line(Doc):
    """A document on its own line, indented some number of spaces."""
    indent: int
    suffix: Doc

    @staticmethod
    def soft(i: int, sep: str, doc: Doc):
        "Either insert a new line after the document, or separate it onto its own line."
        return (Text(sep) + doc) | Line(i, doc)

    @staticmethod
    def softline(i: int, doc: Doc):
        "Either insert a new line after the document, or separate it with a space."
        return Line.soft(i, " ", doc)


@dataclass
class Union(Doc):
    """The non-deterministic choice of two documents, both of which must flatten to
    the same canonical document."""
    d1: Doc
    d2: Doc
