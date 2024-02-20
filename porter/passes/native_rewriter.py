from porter.ast import Binding, sorts, terms
from porter.ast.sorts import Sort
from porter.ast.sorts.visitor import Visitor as SortVisitor
from porter.ast.terms.visitor import SortVisitorOverTerms

from porter.ivy import Position

from typing import Optional

FileLine = tuple[str, int]


def visit(prog: terms.Program):
    remap = {
        ("collections.ivy", 923): "HashSet<`0`>",  # TODO: this is wrong
        ("collections.ivy", 939): "`0`.add(`1`)",
        ("collections.ivy", 945): "`0`.contains(`1`)",
        ("collections.ivy", 952): "TODO",
        ("collections.ivy", 971): "TODO",
        ("collections.ivy", 988): "TODO",
        ("collections.ivy", 1000): "TODO",
        ("collections_impl.ivy", 6): "ArrayList<`0`>",
        ("collections_impl.ivy", 17): """
            `2`.ensureCapacity(`0`);
            for (int _internal_i = 0; i < `0`; _internal_i++) {
                `2`.set(_internal_i, `1`);
            }""",
        ("collections_impl.ivy", 25): "/* */",
        ("collections_impl.ivy", 37): """
            if (0 <= `1` && `1` < `0`.size()) {
                `2` = `0`.get(`1`);
            }""",
        ("collections_impl.ivy", 44): "`1` = `0`.size();",
        ("collections_impl.ivy", 50): """
            int _old_size = `0`.size();
            for (int _internal_i = _old_size; i < `1`; _internal_i++) {
                `0`.set(_internal_i, `2`);
            }""",
        ("collections_impl.ivy", 75): "`0`.add(`1`)",
        ("tcp_serdes.ivy", 506): "HashMap<Integer, Object>",
        ("tcp_serdes.ivy", 508): "TODO",
        ("tcp_serdes.ivy", 510): "TODO"
    }
    nr = NativeRewriter("java", remap)
    nr.visit_program(prog)
    nr.visit_program_sorts(prog, NativeRewriter.NativeSortRewriter("java", remap))


class NativeRewriter(SortVisitorOverTerms):
    class NativeSortRewriter(SortVisitor[Sort]):
        new_lang: str
        mapping: dict[FileLine, str]

        def __init__(self, new_lang: str, mapping: dict[FileLine, str]):
            self.new_lang = new_lang
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
            pos = loc.origin()
            file = pos.filename.name
            line = pos.line

            if (file, line) in self.mapping:
                remapped = self.mapping[(file, line)]
                fmt = remapped
                return sorts.Native(loc, fmt, args)
            else:
                raise Exception(f"No Native remapping for {file}:{line}")
            # return sorts.Native(loc, fmt, args)

        def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
            return sorts.Number(name, lo, hi)

        def _finish_record(self, rec: sorts.Record, fields: dict[str, Sort]):
            return sorts.Record(rec.name, fields)

        def uninterpreted(self, name: str) -> Sort:
            if name in self.mapping:
                return self.visit_sort(self.mapping[name])
            return sorts.Uninterpreted(name)

    new_lang: str
    mapping: dict[FileLine, str]
    sort_visitor: NativeSortRewriter

    def __init__(self, new_lang: str, mapping: dict[FileLine, str]):
        self.new_lang = new_lang
        self.mapping = mapping
        self.sort_visitor = self.NativeSortRewriter(new_lang, mapping)

    def _finish_native(self, act: terms.Native, args: list[None]):
        pos = act.pos()
        assert pos
        file = pos.origin().filename.name
        line = pos.origin().line

        if (file, line) in self.mapping:
            remapped = self.mapping[(file, line)]
            act.lang = self.new_lang
            act.fmt = remapped
        else:
            raise Exception(f"No Native remapping for {file}:{line}")
