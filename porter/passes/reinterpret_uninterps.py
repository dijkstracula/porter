from porter.ast import sorts
from porter.ast.sorts import Sort
from porter.ast.sorts.visitor import Visitor as SortVisitor

from typing import Optional

from porter.ivy import Position


class InterpretUninterpretedVisitor(SortVisitor[Sort]):
    "Walks a sort and replaces all annotated Uninterpreted sorts with another one."
    # TODO: This does more than what the class name suggests, so we should rename it.

    mapping: dict[str, Sort]

    def __init__(self, mapping: dict[str, Sort]):
        self.mapping = mapping

    def bool(self) -> Sort:
        return sorts.Bool()

    def bv(self, width: int) -> Sort:
        return sorts.BitVec(width)

    def enum(self, name: str, discriminants: tuple[str, ...]) -> Sort:
        return sorts.Enum(name, discriminants)

    def _begin_function(self, node: sorts.Function):
        pass

    def _finish_function(self, node: sorts.Function, domain: list[Sort], range: Sort) -> Sort:
        return sorts.Function(domain, range)

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        if name in self.mapping:
            return self.mapping[name]
        return sorts.Number(name, lo, hi)

    def _finish_native(self, loc: Position, fmt: str, args: list[str]):
        return sorts.Native(loc, fmt, args)

    def _finish_record(self, rec: sorts.Record, fields: dict[str, Sort]):
        return sorts.Record(rec.name, fields)

    def uninterpreted(self, name: str) -> Sort:
        if name in self.mapping:
            return self.visit_sort(self.mapping[name])
        return sorts.Uninterpreted(name)


