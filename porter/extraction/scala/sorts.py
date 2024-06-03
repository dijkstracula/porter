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
        iters = [BeguineKind().visit_sort(a) for a in node.domain]
        return Text("new ") + \
            UnboxedSort().visit_sort(node) + \
            utils.enclosed("(", utils.join(iters, ", "), ")")

    def _begin_native(self, nat: sorts.Native) -> Optional[Doc]:
        # XXX: Presumably we will have a few special-cased native default
        # values.  Maybe this should live as part of native_rewriter?
        if nat.fmt.startswith("mutable.ArraySeq"):
            return Text("mutable.ArraySeq.empty")
        pass

    def _finish_native(self, lang: str, fmt: str, args: list[Doc]):
        # return Text("new ") + interpolate_native(fmt, args) + Text("()")
        return Text("null")  # XXX: Assumes native types are reference types, is this ok?

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        if lo:
            return Text(str(lo))
        return Text("0")

    def _finish_record(self, rec: sorts.Record, fields: dict[str, Doc]):
        return Text("new " + canonicalize_identifier(rec.sort_name) + "()")

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
        return Text("new beguine.Maps.Map") + Text(str(len(domain)))  # TODO: generics

    def _finish_native(self, lang: str, fmt: str, args: list[Doc]):
        return interpolate_native(fmt, args)

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        return Text("Int")

    def _finish_record(self, rec: sorts.Record, fields: dict[str, Doc]):
        return Text(canonicalize_identifier(rec.sort_name))

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
        return Text(canonicalize_identifier(rec.sort_name))

    def top(self):
        return Text("Unit")

    def uninterpreted(self, name: str):
        return Text("Int")


class SortDeclaration(SortVisitor[Doc]):
    """Many sorts don't need explicit declarations extracted, but here are the ones that do. """

    @staticmethod
    def record_companion_class(rec: sorts.Record) -> Doc:
        name = Text(canonicalize_identifier(rec.sort_name))
        ret = Text("object ") + name + Text(" extends sorts.Record[") + name + Text("]")

        agen = ArbitraryGenerator("a")
        body = agen.gen_signature() + utils.padded("=") + \
               utils.enclosed("{", agen.record_gen_body(rec), "}")

        ret = ret + utils.enclosed("{", body, "}")
        return ret

    @staticmethod
    def record_equal_body(rec: sorts.Record) -> Doc:
        name = Text(canonicalize_identifier(rec.sort_name))
        poscase = Text("case that:") + utils.padded(name) + Text("=>") + utils.space
        poscase = poscase + Text("that.canEqual(this)")
        for name, sort in rec.fields.items():
            name = Text(canonicalize_identifier(name))
            poscase = poscase + utils.soft_line + Text("&&") + utils.space + \
                      name + utils.padded("==") + Text("that.") + name
        negcase = Text("case _ => false")

        return Text("other match ") + \
            utils.enclosed("{", poscase + Line() + negcase, "}")

    @staticmethod
    def record_equals_preds(rec: sorts.Record) -> Doc:
        name = Text(canonicalize_identifier(rec.sort_name))
        canEqualDef = Text("private def canEqual(other: Any): Boolean = other.isInstanceOf[") + name + Text("]")
        equalsDef = Text("override def equals(other: Any) = ") + \
                    utils.enclosed("{", SortDeclaration.record_equal_body(rec), "}")

        return canEqualDef + Line() + equalsDef

    @staticmethod
    def record_hashcode(rec: sorts.Record) -> Doc:
        fold = Text("state.map(_.hashCode()).foldLeft(0)((a, b) => 31 * a + b)")

        body = Text("val state = Seq") + \
               utils.enclosed("(",
                              utils.join([Text(canonicalize_identifier(n)) for n in rec.fields], ", "),
                              ")")
        return Text("override def hashCode(): Int = ") + \
            utils.enclosed("{", body + Line() + fold, "}")


    @staticmethod
    def record_tostring(rec: sorts.Record) -> Doc:
        state = Text("val state = Seq") + \
               utils.enclosed("(",
                              utils.join([Text(canonicalize_identifier(n)) for n in rec.fields], ", "),
                              ")")

        pre = utils.enclosed("\"", Text(rec.sort_name) + Text("("), "\"")
        fold = Text('state.foldLeft("")((a, b) => a + ", " + b)')
        post = utils.enclosed("\"", Text(")"), "\"")
        ret_stmt = utils.join([pre, fold, post], Text(" + "))

        return Text("override def toString = ") + \
            utils.enclosed("{", state + Line() + ret_stmt, "}")

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
        recname = canonicalize_identifier(rec.sort_name)
        field_docs = [Text("var") + space +
                      Text(canonicalize_identifier(name)) + \
                      Text(": ") + UnboxedSort().visit_sort(s) + \
                      Text(" == ") + DefaultValue().visit_sort(s)
                      for name, s in rec.fields.items()]
        preds = [Line(),
                 SortDeclaration.record_equals_preds(rec),
                 SortDeclaration.record_hashcode(rec),
                 SortDeclaration.record_tostring(rec)]

        clazz_decl = Text("class " + recname) + \
                     utils.padded("{") + Line() + \
                     Nest(4, utils.join(field_docs + preds, "\n")) + Line() + \
                     Line() + Text("}")

        # TODO: look at how something like shapeless might help with this.
        return clazz_decl + Line() + SortDeclaration.record_companion_class(rec) + Line()

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
        return Text(canonicalize_identifier(name))

    def _finish_function(self, node: sorts.Function, domain: list[Doc], range: Doc):
        return Text("TODO")

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        return Text(canonicalize_identifier(name))

    def _begin_native(self, nat: sorts.Native):
        if nat.fmt.startswith("mutable.ArraySeq"):
            return Text("mutable.ArraySeq.empty")

    def _finish_native(self, lang: str, fmt: str, args: list[Doc]):
        return Text("TODO (native sort kind)")  # TODO: should this be a typedef or something?

    def _finish_record(self, rec: sorts.Record, fields: dict[str, Doc]):
        return Text(canonicalize_identifier(rec.sort_name))

    def top(self):
        return Text("sorts.Top()")

    def uninterpreted(self, name: str):
        return Text(canonicalize_identifier(name))


class ArbitraryGenerator(SortVisitor[Doc]):
    "Produces an expression to invoke an Arbitrary to generate a value of a given Sort."

    arbitrary_name: Doc

    def gen_signature(self) -> Doc:
        return Text(f"override def arbitrary(implicit") + utils.padded(self.arbitrary_name) + Text(": Arbitrary)")

    def record_gen_body(self, rec: sorts.Record) -> Doc:
        hdr = Text(f"val ret = new {canonicalize_identifier(rec.sort_name)}") + Line()

        body = Nil()
        for name, sort in rec.fields.items():
            body = body + Text(f"ret.{canonicalize_identifier(name)} = ") + self.visit_sort(sort) + Line()

        ftr = Text("ret")
        return hdr + body + ftr

    def __init__(self, arbitrary_name: str):
        self.arbitrary_name = Text(arbitrary_name)

    def bool(self) -> Doc:
        return self.arbitrary_name + Text(f".bool()")

    def bv(self, width: int) -> Doc:
        return self.arbitrary_name + Text(f".bitvec(sorts.BitVec({width}))")

    def enum(self, name: str, discriminants: tuple[str, ...]):
        return self.arbitrary_name + Text(f".enumeration(Enum({name})")

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        # XXX:
        return self.arbitrary_name + Text(f".numeric({name})")

    def _begin_record(self, rec: sorts.Record) -> Optional[Doc]:
        return Text(rec.sort_name)

    def _finish_native(self, loc: Position, fmt: str, args: list[Doc]):
        return Text("TODO (native arbitrary)" + fmt + str(args))

    def uninterpreted(self, name: str) -> Doc:
        return self.arbitrary_name + Text(f".uninterpreted")
