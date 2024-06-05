from . import *

import re


def interpolate_native(fmt: str, args: list[Doc]):
    pat = r"`(\d+)`"
    ret = Nil()

    for line in fmt.split("\n"):
        line = line.strip()
        if line == "":
            continue

        if not isinstance(ret, Nil):
            ret = ret + Line()

        # TODO: bail out if we have not translated the Native out of C++.
        curr_begin = 0
        m = re.search(pat, line[curr_begin:])
        while m:
            idx = int(m.group(1))
            text = line[curr_begin: curr_begin + m.start()]
            text = re.sub(r"\s+", " ", text)
            ret = ret + Text(text) + args[idx]

            curr_begin = curr_begin + m.end()
            m = re.search(pat, line[curr_begin:])

        final = line[curr_begin:]
        if final != "":
            ret = ret + Text(final)
    return ret


# A formatter consumes a Document that may contain Choices,
# and chooses between them such that the resulting Document
# does not contain Choices.

class Formatter:
    width: int

    def __init__(self, w: int):
        self.width = w

    def format(self, d: Doc) -> Doc:
        raise NotImplementedError


class Naive(Formatter):
    curr_indent = 0
    curr_column = 0

    def naive_iter(self, d: Doc) -> Doc:
        match d:
            case Nil():
                return Nil()
            case Text("\n") | Line():
                self.curr_column = self.curr_indent
                return Text("\n" + " " * self.curr_indent)
            case Text(_):
                return d
            case Concat(lhs, rhs):
                lhs = self.naive_iter(lhs)
                self.curr_column += lhs.length()
                rhs = self.naive_iter(rhs)  # This is wrong but I'm also very stupid
                return Concat(lhs, rhs)
            case Nest(i, d):
                self.curr_indent += i
                ret = Nest(i, self.naive_iter(d))
                self.curr_indent -= i
                return ret
            case Choice(d1, d2):
                d1 = self.naive_iter(d1)
                if d1.fits(self.width - self.curr_column):
                    return d1
                else:
                    # TODO: if neither fits, we could consider flattening and retrying?
                    return self.naive_iter(d2)
        raise NotImplementedError(d)

    def format(self, d: Doc) -> Doc:
        self.curr_indent = 0
        return simpl(self.naive_iter(simpl(d)))
