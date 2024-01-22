from . import *


# A formatter consumes a Document that may contain Choices,
# and chooses between them such that the resulting Document
# does not contain Choices.

def naive(w: int, k: int, d: Doc) -> Doc:
    "Wadler's naive formatter, requiring potentially O(n^2) time complexity."
    match d:
        case Nil():
            return Nil()
        case Text(s):
            return Text(s)
        case Line():
            return Line()
        case Concat(lhs, rhs):
            lhs = naive(w, k, lhs)
            rhs = naive(w, k + lhs.length(), rhs)
            return Concat(lhs, rhs)
        case Nest(i, d):
            return Nest(i, naive(w, i, d))
        case Choice(d1, d2):
            # TODO: if neither fits, we could consider flattening and retrying?
            if d1.fits(w - k):
                return d1
            else:
                return d2
    assert False
