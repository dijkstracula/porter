""" The world's most naive pretty-printing combinators, after
Wadler (https://homepages.inf.ed.ac.uk/wadler/papers/prettier/prettier.pdf). """

from dataclasses import dataclass


class Doc:
    def __add__(self, other: "Doc") -> "Doc":
        "Sugar for horizontal concatenation."
        return Concat(self, other)

    def __or__(self, other: "Doc") -> "Doc":
        "Sugar for choice."
        return Choice(self, other)

    def layout(self) -> str:
        """Converts a document to a string. """
        match self:
            case Nil():
                return ""
            case Concat(lhs, rhs):
                return lhs.layout() + rhs.layout()
            case Text(s):
                return s
            case Line():
                return "\n"
            case Nest(i, d):
                return Line().layout() + (" " * i) + d.layout()
            case Choice(_, _):
                raise Exception("TODO: non-canonical layout - did you receive this Doc from a formatter?")
        assert False

    def length(self) -> int:
        """The length of a canonicalized document. """
        match self:
            case Nil():
                return 0
            case Concat(lhs, rhs):
                return lhs.length() + rhs.length()
            case Text(s):
                return len(s)
            case Line():
                return 0
            case Nest(i, d):
                return i + d.length()
            case Choice(_, _):
                raise Exception("TODO: non-canonical layout - did you receive this Doc from a formatter?")
        assert False

    def fits(self, width: int) -> bool:
        if width < 0:
            return False
        match self:
            case Nil():
                return True
            case Line():
                return True
            case Text(s):
                return len(s) <= width
            case Concat(lhs, rhs):
                return rhs.fits(width - lhs.length())
            case Choice(lhs, rhs):
                return lhs.fits(width) or rhs.fits(width)  # TODO: is this right?
        assert False

    def group(self) -> "Doc":
        """Produces the layout of the doc, where the layouts may be
        compressed onto a single line."""
        return self.flatten() | self

    def flatten(self) -> "Doc":
        """Replaces all line breaks with a single space."""
        match self:
            case Nil():
                return Nil()
            case Concat(lhs, rhs):
                return Concat(lhs.flatten(), rhs.flatten())
            case Text(s):
                return Text(s)
            case Line():
                return Text(" ")
            case Nest(_, x):
                return Text(" ") + x.flatten()
            case Choice(d1, _):
                return d1.flatten()
        assert False


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
    "A newline literal."
    pass


@dataclass
class Nest(Doc):
    """A document on its own line, indented some number of spaces."""
    indent: int
    suffix: Doc


@dataclass
class Choice(Doc):
    """The non-deterministic choice of two documents, both of which must flatten to
    the same canonical document.  (Wadler's Union)"""
    # TODO: Contemplate factoring this out into an Iterable[Doc] and be explicit about
    # Doc being a _canonicalized_ format so we don't have to have runtime failures if
    # we try to e.g. take the length of a Choice.
    d1: Doc
    d2: Doc
