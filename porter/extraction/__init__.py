from porter.ast import terms
from porter.extraction import scala
from porter.pp import formatter


def extract_scala(prog: terms.Program, width=200) -> str:
    doc = scala.extract("PorterIsolate", prog)
    return formatter.Naive(width).format(doc).layout()
