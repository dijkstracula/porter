from . import *


# A formatter consumes a Document that may contain Choices,
# and chooses between them such that the resulting Document
# does not contain Choices.

class Formatter:
    width: int

    def __init__(self, w: int):
        self.width = w

    def format(self, d: Doc) -> Doc:
        raise NotImplementedError


def simpl(d: Doc) -> Doc:
    "A summary of a bunch of Wadler's laws."
    match d:
        case Nil():
            return Nil()
        case Line():
            return Line()
        case Text("\n"):
            return Line()
        case Text(s):
            return Text(s)
        case Concat(lhs, rhs):
            match lhs, rhs:
                case Concat(l, r), rhs:
                    return simpl(Concat(l, Concat(r, rhs)))

            lhs = simpl(lhs)
            rhs = simpl(rhs)
            match (lhs, rhs):
                case Nil() | Text(""), rhs:
                    return rhs
                case lhs, Nil() | Text(""):
                    return lhs
                case Text(lhs), Text(rhs):
                    return Text(lhs + rhs)
                case Text(l), Concat(Text(r), rhs):
                    return Concat(Text(l + r), rhs)
                case lhs, rhs:
                    return Concat(lhs, rhs)
        case Nest(i, d):
            d = simpl(d)
            if i == 0:
                return d
            match d:
                case Nil():
                    return Nil()
                case Line():
                    return Line()
                case Nest(j, d2):
                    return Nest(i + j, d2)
                case d:
                    return Nest(i, d)
        case Choice(d1, d2):
            d1 = simpl(d1)
            d2 = simpl(d2)
            match (d1, d2):
                case d1, Nil():
                    return d1
                case Nil(), d2:
                    return d2
                case d1, d2:
                    return Choice(d1, d2)


class Naive(Formatter):
    curr_indent = 0

    def naive_iter(self, k: int, d: Doc) -> Doc:
        match d:
            case Nil():
                return Nil()
            case Text("\n") | Line():
                return Text("\n" + " " * self.curr_indent)
            case Text(s):
                return Text(s)
            case Concat(lhs, rhs):
                lhs = self.naive_iter(k, lhs)
                rhs = self.naive_iter(k, rhs)  # This is wrong but I'm also very stupid
                return Concat(lhs, rhs)
            case Nest(i, d):
                self.curr_indent += i
                ret = Nest(i, self.naive_iter(i + k, d))
                self.curr_indent -= i
                return ret
            case Choice(d1, d2):
                d1 = self.naive_iter(k, d1)
                if d1.fits(self.width - k):
                    return d1
                else:
                    # TODO: if neither fits, we could consider flattening and retrying?
                    return self.naive_iter(k, d2)
        raise NotImplementedError(d)

    def format(self, d: Doc) -> Doc:
        self.curr_indent = 0
        return simpl(self.naive_iter(0, simpl(d)))
