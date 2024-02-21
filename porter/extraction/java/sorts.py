from .utils import *

from porter.ast import sorts

from porter.ast.sorts.visitor import Visitor as SortVisitor

from porter.pp import Doc, Text, Nil, utils
from porter.pp.formatter import interpolate_native
from porter.pp.utils import space

from typing import Optional


class DefaultValue(SortVisitor[Doc]):
    def bool(self):
        return Text("false")

    def bv(self, name: str, width: int):
        if width > 64:
            raise Exception("BV too wide")
        if width > 8:
            return Text("0L")
        return Text("0")

    def enum(self, name: str, discriminants: list[str]):
        return Text(canonicalize_identifier(discriminants[0]))

    def native(self, lang: str, fmt: str, args: list[str]):
        return Text("new ") + interpolate_native(fmt, [Text(arg) for arg in args]) + Text("()")

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        if lo:
            return Text(str(lo))
        return Text("0")

    def _finish_record(self, rec: sorts.Record, fields: dict[str, Doc]):
        return Text("new " + canonicalize_identifier(rec.name) + "()")

    def uninterpreted(self, name: str):
        return Text("0")


class BoxedSort(SortVisitor[Doc]):
    def bool(self):
        return Text("Boolean")

    def bv(self, name: str, width: int):
        if width > 64:
            raise Exception("BV too wide")
        if width > 8:
            return Text("Long")
        return Text("Byte")

    def enum(self, name: str, discriminants: list[str]):
        return Text(name)

    def _finish_function(self, node: sorts.Function, domain: list[Doc], range: Doc):
        return Text("Action") + Text(str(len(domain) + 1))  # TODO: generics

    def native(self, lang: str, fmt: str, args: list[str]):
        return interpolate_native(fmt, [Text(arg) for arg in args])

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        return Text("Integer")

    def _finish_record(self, rec: sorts.Record, fields: dict[str, Doc]):
        return Text(canonicalize_identifier(rec.name))

    def top(self):
        return Text("Void")

    def uninterpreted(self, name: str):
        return Text("Integer")


class UnboxedSort(SortVisitor[Doc]):
    def bool(self):
        return Text("boolean")

    def bv(self, name: str, width: int):
        if width > 64:
            raise Exception("BV too wide")
        if width > 8:
            return Text("long")
        return Text("byte")

    def enum(self, name: str, discriminants: list[str]):
        return Text(canonicalize_identifier(name))

    def _finish_function(self, node: sorts.Function, _domain: list[Doc], _range: Doc):
        boxed = BoxedSort()
        type_args = [boxed.visit_sort(s) for s in node.domain + [node.range]]

        cls = Text("Function") + Text(str(len(type_args)))
        return cls + utils.enclosed("<", utils.join(type_args, ", "), ">")

    def native(self, lang: str, fmt: str, args: list[str]):
        return interpolate_native(fmt, [Text(arg) for arg in args])

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        return Text("int")

    def _finish_record(self, rec: sorts.Record, fields: dict[str, Doc]):
        return Text(canonicalize_identifier(rec.name))

    def top(self):
        return Text("void")

    def uninterpreted(self, name: str):
        return Text("int")


class SortDeclaration(SortVisitor[Doc]):
    """Many sorts don't need explicit declarations extracted, but here are the ones that do. """

    def bool(self):
        return Nil()

    def bv(self, name: str, width: int):
        return Nil()

    def enum(self, name: str, discriminants: list[str]):
        discs = utils.join([Text(canonicalize_identifier(s)) for s in discriminants], utils.soft_comma)
        return Text("public enum ") + Text(canonicalize_identifier(name)) + space + block(discs)

    def _finish_function(self, node: sorts.Function, domain: list[Doc], range: Doc):
        boxed = BoxedSort()
        type_args = [boxed.visit_sort(s) for s in node.domain + [node.range]]

        cls = Text("Function") + Text(str(len(type_args)))
        return cls + utils.enclosed("<", utils.join(type_args, ", "), ">")

    def native(self, lang: str, fmt: str, args: list[str]):
        return Nil()  # TODO: should this be a typedef or something?

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        return Nil()

    def _finish_record(self, rec: sorts.Record, fields: dict[str, Doc]):
        unboxed = UnboxedSort()
        field_docs = [Text("public") + space +
                      unboxed.visit_sort(s) + space +
                      Text(canonicalize_identifier(name)) + Text(";") for name, s in rec.fields.items()]
        return Text("public class " + canonicalize_identifier(rec.name)) + space + block(utils.join(field_docs, "\n"))

    def top(self):
        return Text("void")

    def uninterpreted(self, name: str):
        return Nil()
