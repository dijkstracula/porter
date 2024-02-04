from .utils import *

from porter.ast import sorts

from porter.ast.sorts.visitor import Visitor as SortVisitor

from porter.pp import Doc, Text, Nil, utils
from porter.pp.utils import space

from typing import Optional


class BoxedSort(SortVisitor[Doc]):
    def bool(self):
        return Text("Boolean")

    def bv(self, name: str, width: int):
        if width > 64:
            raise Exception("BV too wide")
        return Text("Long")

    def enum(self, name: str, discriminants: list[str]):
        return Text(name)

    def _finish_function(self, node: sorts.Function, domain: list[Doc], range: Doc):
        return Text("Action") + Text(str(len(domain) + 1))  # TODO: generics

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        return Text("Integer")

    def uninterpreted(self, name: str):
        return Text("Integer")


class UnboxedSort(SortVisitor[Doc]):
    def bool(self):
        return Text("bool")

    def bv(self, name: str, width: int):
        if width > 64:
            raise Exception("BV too wide")
        return Text("long")

    def enum(self, name: str, discriminants: list[str]):
        return Text(name)

    def _finish_function(self, node: sorts.Function, _domain: list[Doc], _range: Doc):
        boxed = BoxedSort()
        type_args = [boxed.visit_sort(s) for s in node.domain + [node.range]]

        cls = Text("Function") + Text(str(len(type_args)))
        return cls + utils.enclosed("<", utils.join(type_args, ", "), ">")

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        return Text("int")

    def uninterpreted(self, name: str):
        return Text("int")


class SortDeclaration(SortVisitor[Doc]):
    """Many sorts don't need explicit declarations extracted, but here are the ones that do. """

    def bool(self):
        return Nil()

    def bv(self, name: str, width: int):
        return Nil()

    def enum(self, name: str, discriminants: list[str]):
        discs = utils.join([Text(s) for s in discriminants], utils.soft_comma)
        return Text("public enum ") + Text(name) + space + block(discs)

    def _finish_function(self, node: sorts.Function, domain: list[Doc], range: Doc):
        boxed = BoxedSort()
        type_args = [boxed.visit_sort(s) for s in node.domain + [node.range]]

        cls = Text("Function") + Text(str(len(type_args)))
        return cls + utils.enclosed("<", utils.join(type_args, ", "), ">")

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        return Nil()

    def uninterpreted(self, name: str):
        return Nil()
