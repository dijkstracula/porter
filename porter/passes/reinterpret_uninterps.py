from porter.ast import sorts
from porter.ast.sorts import Sort
from porter.ast.sorts.visitor import Visitor as SortVisitor
from porter.ast import Binding, terms
from porter.ast.terms.visitor import MutVisitor as TermMutVisitor

from typing import Optional

from porter.ivy import Position


class ReinterpretUninterpsSortVisitor(SortVisitor[Sort]):
    "Walks a sort and replaces all annotated Uninterpreted sorts with another one."
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

    def native(self, loc: Position, fmt: str, args: list[str]):
        return sorts.Native(loc, fmt, args)

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        return sorts.Number(name, lo, hi)

    def _finish_record(self, rec: sorts.Record, fields: dict[str, Sort]):
        return sorts.Record(rec.name, fields)

    def uninterpreted(self, name: str) -> Sort:
        if name in self.mapping:
            return self.visit_sort(self.mapping[name])
        return sorts.Uninterpreted(name)


class ReinterpretUninterpreted(TermMutVisitor):
    sort_visitor: ReinterpretUninterpsSortVisitor

    def __init__(self, mapping: dict[str, Sort]):
        self.sort_visitor = ReinterpretUninterpsSortVisitor(mapping)

    def _finish_apply(self, node: terms.Apply, relsym_ret: None, args_ret: list[None]):
        if len(node.args) > 0:
            possibly_self = node.args[0]
            s = possibly_self.sort()
            if s:
                possibly_self._sort = self.sort_visitor.visit_sort(s)

    def _finish_let(self, act: terms.Let, scope: None):
        act.vardecls = [Binding(b.name, self.sort_visitor.visit_sort(b.decl)) for b in act.vardecls]

    def _finish_action_def(self, name: str, defn: terms.ActionDefinition, body: None):
        defn.formal_params = [Binding(b.name, self.sort_visitor.visit_sort(b.decl)) for b in defn.formal_params]
        defn.formal_returns = [Binding(b.name, self.sort_visitor.visit_sort(b.decl)) for b in defn.formal_returns]
        pass
