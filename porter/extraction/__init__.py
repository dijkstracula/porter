from porter.ast import terms
from porter.extraction import scala
from porter.pp import formatter


def extract_java(prog: terms.Program, width=80) -> str:
    doc = scala.extract("PorterIsolate", prog)
    return formatter.Naive(width).format(doc).layout()
