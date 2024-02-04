from porter.ast import terms
from porter.extraction import java
from porter.pp import formatter


def extract_java(prog: terms.Program, width=80) -> str:
    doc = java.extract("PorterIsolate", prog)
    return formatter.Naive(width).format(doc).layout()
