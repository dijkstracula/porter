from .utils import *

from porter.ast import sorts

from porter.ast.sorts.visitor import Visitor as SortVisitor

from porter.ivy import Position

from porter.pp import Doc, Text, Nil, utils
from porter.pp.formatter import interpolate_native
from porter.pp.utils import space

from typing import Optional


class DefaultValue(SortVisitor[Doc]):
    "A sensible initializer value for values of a given sort."

    def bool(self):
        return Text("false")

    def bv(self, width: int):
        if width > 64:
            raise Exception("BV too wide")
        if width > 8:
            return Text("0L")
        return Text("0")

    def enum(self, name: str, discriminants: list[str]):
        return Text(canonicalize_identifier(discriminants[0]))

    def _finish_function(self, node: sorts.Function, domain: list[Doc], range: Doc) -> Doc:
        return UnboxedSort().visit_sort(node) + Text("()")

    def _finish_native(self, lang: str, fmt: str, args: list[Doc]):
        # return Text("new ") + interpolate_native(fmt, args) + Text("()")
        return Text("null")  # XXX: Assumes native types are reference types, is this ok?

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        if lo:
            return Text(str(lo))
        return Text("0")

    def _finish_record(self, rec: sorts.Record, fields: dict[str, Doc]):
        return Text("new " + canonicalize_identifier(rec.name) + "()")

    def top(self):
        return Text("null")

    def uninterpreted(self, name: str):
        return Text("0")


class BoxedSort(SortVisitor[Doc]):
    "A reference type for a given sort"

    def bool(self):
        return Text("Boolean")

    def bv(self, width: int):
        if width > 64:
            raise Exception("BV too wide")
        if width > 8:
            return Text("Long")
        return Text("Byte")

    def enum(self, name: str, discriminants: list[str]):
        return Text(name)

    def _finish_function(self, node: sorts.Function, domain: list[Doc], range: Doc):
        return Text("beguine.Maps.Map") + Text(str(len(domain)))  # TODO: generics

    def _finish_native(self, lang: str, fmt: str, args: list[Doc]):
        return interpolate_native(fmt, args)

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        return Text("Int")

    def _finish_record(self, rec: sorts.Record, fields: dict[str, Doc]):
        return Text(canonicalize_identifier(rec.name))

    def top(self):
        return Text("Void")

    def uninterpreted(self, name: str):
        return Text("Integer")


class UnboxedSort(SortVisitor[Doc]):
    "A value type for a given sort."

    def bool(self):
        return Text("Boolean")

    def bv(self, width: int):
        if width > 64:
            raise Exception("BV too wide")
        if width > 8:
            return Text("Long")
        return Text("Byte")

    def enum(self, name: str, discriminants: list[str]):
        return Text(canonicalize_identifier(name))

    def _begin_function(self, node: sorts.Function) -> Optional[Doc]:
        type_args = [self.visit_sort(s) for s in node.domain + [node.range]]

        cls = Text("Maps.Map") + Text(str(len(node.domain)))
        return cls + utils.enclosed("[", utils.join(type_args, ", "), "]")

    def _finish_native(self, lang: str, fmt: str, args: list[Doc]):
        return interpolate_native(fmt, args)

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        return Text("Int")

    def _finish_record(self, rec: sorts.Record, fields: dict[str, Doc]):
        return Text(canonicalize_identifier(rec.name))

    def top(self):
        return Text("Unit")

    def uninterpreted(self, name: str):
        return Text("Int")


class SortDeclaration(SortVisitor[Doc]):
    """Many sorts don't need explicit declarations extracted, but here are the ones that do. """

    def bool(self):
        return Nil()

    def bv(self, width: int):
        return Nil()

    def enum(self, name: str, discriminants: list[str]):
        name = canonicalize_identifier(name)
        typ = Text(f"type {name} = Value")
        discs = Text("val ") + utils.join([Text(canonicalize_identifier(s)) for s in discriminants],
                                          utils.soft_comma) + Text(" = Value")
        imp = Text(f"import {name}._")

        return Text("object") + utils.padded(Text(canonicalize_identifier(name))) + Text("extends Enumeration ") + \
            utils.enclosed("{", typ + Line() + discs, "}") + Line() + imp

    def _finish_function(self, node: sorts.Function, domain: list[Doc], range: Doc):
        boxed = BoxedSort()
        type_args = [boxed.visit_sort(s) for s in node.domain + [node.range]]

        cls = Text("beguine.Maps.Map") + Text(str(len(node.domain)))
        return cls + utils.enclosed("[", utils.join(type_args, ", "), "]")

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        name = canonicalize_identifier(name)
        lo_str = "Int.MinValue" if lo is None else f"{lo}"
        hi_str = "Int.MaxValue" if hi is None else f"{hi}"
        return Text(f"val {name} = beguine.sorts.Number({lo_str}, {hi_str})")

    def _finish_native(self, lang: str, fmt: str, args: list[Doc]):
        return Nil()  # TODO: should this be a typedef or something?

    def _finish_record(self, rec: sorts.Record, fields: dict[str, Doc]):
        recname = canonicalize_identifier(rec.name)
        field_docs = [Text("var") + space +
                      Text(canonicalize_identifier(name)) + \
                      Text(": ") + UnboxedSort().visit_sort(s) + \
                      Text(" = ") + DefaultValue().visit_sort(s)
                      for name, s in rec.fields.items()]
        clazz_decl = Text("class " + recname) + utils.soft_line + utils.enclosed("{", utils.join(field_docs, "\n"), "}")

        # TODO: look at how something like shapeless might help with this.
        metaclass_decl = Text("class ") + Text(record_metaclass_name(recname)) + \
                         Text(" extends sorts.Record[") + Text(recname) + Text("] {}")

        return clazz_decl + Line() + metaclass_decl + Line()

    def top(self):
        return Text("Void")

    def uninterpreted(self, name: str):
        return Nil()


class BeguineKind(SortVisitor[Doc]):
    "Produces the class name for the sort metaclass (eg. sorts.Numeric(0, 3)). (TODO: this vs arbitrarygen?)"

    def bool(self):
        return Text("sorts.Boolean()")

    def bv(self, width: int):
        return Text(f"sorts.BitVec({width})")

    def enum(self, name: str, discriminants: list[str]):
        return Text(f"sorts.Enum[{name}]()")

    def _finish_function(self, node: sorts.Function, domain: list[Doc], range: Doc):
        return Text("TODO")

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        lo_str = "Int.MinValue" if lo is None else f"{lo}"
        hi_str = "Int.MaxValue" if hi is None else f"{hi}"
        return Text(f"sorts.Number({lo_str}, {hi_str})")

    def _finish_native(self, lang: str, fmt: str, args: list[Doc]):
        return Text("TODO (native sort kind)")  # TODO: should this be a typedef or something?

    def _finish_record(self, rec: sorts.Record, fields: dict[str, Doc]):
        return Text("TODO (record sort kind)")

    def top(self):
        return Text("sorts.Top()")

    def uninterpreted(self, name: str):
        return Text("sorts.Uninterpreted()")


class ArbitraryGenerator(SortVisitor[Doc]):
    "Produces an expression to invoke an Arbitrary to generate a value of a given Sort."

    arbitrary_name: Doc

    def __init__(self, arbitrary_name: str):
        self.arbitrary_name = Text(arbitrary_name)

    def bool(self) -> Doc:
        return self.arbitrary_name + Text(f".bool()")

    def bv(self, width: int) -> Doc:
        return self.arbitrary_name + Text(f".bitvec(sorts.BitVec({width}))")

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        # XXX:
        return self.arbitrary_name + Text(f".numeric({name})")

    def _begin_record(self, rec: sorts.Record) -> Optional[Doc]:
        return Text(record_metaclass_name(rec.name))

    def _finish_native(self, loc: Position, fmt: str, args: list[Doc]):
        return Text("TODO (native arbitrary)" + str(loc))

    def uninterpreted(self, name: str) -> Doc:
        # raise Exception(f"Sort {name} is marked as uninterpreted; cannot infer a finite bound")
        # TODO: this needs to be smarter... something like a stateful "gradually increasing range" generator??
        return self.arbitrary_name + Text(f".numeric(sorts.Number({-100}, {100})")
