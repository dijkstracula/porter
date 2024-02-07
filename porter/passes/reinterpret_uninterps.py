from porter.ast import sorts
from porter.ast.sorts import Sort
from porter.ast.sorts.visitor import Visitor

from typing import Optional


class ReinterpretUninterps(Visitor[Sort]):
    "Walks a sort and replaces all annotated Uninterpreted sorts with another one."
    mapping: dict[str, Sort]

    def __init__(self, mapping: dict[str, Sort]):
        self.mapping = mapping

    def bool(self) -> Sort:
        return sorts.Bool()

    def bv(self, width: int) -> Sort:
        return sorts.BitVec(width)

    def enum(self, name: str, discriminants: tuple[str, ...]) -> Sort:
        return sorts.Enumeration(name, discriminants)

    def _begin_function(self, node: sorts.Function):
        pass

    def _finish_function(self, node: sorts.Function, domain: list[Sort], range: Sort) -> Sort:
        return sorts.Function(domain, range)

    def native(self, lang: str, fmt: str, args: list[str]):
        return sorts.Native(lang, fmt, args)

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        return sorts.Number(name, lo, hi)

    def _finish_record(self, rec: sorts.Record, fields: dict[str, Sort]):
        return sorts.Record(rec.name, fields)

    def uninterpreted(self, name: str) -> Sort:
        if name in self.mapping:
            return self.visit_sort(self.mapping[name])
        return sorts.Uninterpreted(name)