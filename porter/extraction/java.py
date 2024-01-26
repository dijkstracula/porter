from porter.ast import Binding, sorts, terms

from porter.ast.terms.visitor import Visitor as TermVisitor
from porter.ast.sorts.visitor import Visitor as SortVisitor

from porter.pp import Doc, Text, Line, Nest, Nil, utils

from typing import Optional

semi = Text(";")

soft_open_bracket = Text("{") + utils.soft_line
soft_close_bracket = utils.soft_line + Text("}")


def block(contents: Doc) -> Doc:
    return Text("{") + Line() + Nest(2, contents) + Line() + Text("}")


def canonicalize_identifier(s: str) -> str:
    return s.replace(".", "__")


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

    def _finish_function(self, node: sorts.Function, domain: list[Doc], range: Doc):
        return Text("Action") + Text(str(len(domain) + 1))  # TODO: generics

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
        return Text("public enum ") + Text(name) + utils.space + block(discs)

    def _finish_function(self, node: sorts.Function, domain: list[Doc], range: Doc):
        return Text("Action") + Text(str(len(domain) + 1))  # TODO: generics

    def numeric(self, name: str, lo: Optional[int], hi: Optional[int]):
        return Nil()

    def uninterpreted(self, name: str):
        return Nil()


class Extractor(TermVisitor[Doc]):
    def extract(self, prog: terms.Program) -> Doc:
        self.visit_program(prog)

        sort_declarer = SortDeclaration()
        sorts = [sort_declarer.visit_sort(s) for name, s in self.sorts.items()]
        sorts = utils.join(sorts, "\n")

        inits = utils.join(self.inits, "\n")

        return sorts + Text("\n\n\n") + inits

    # Expressions

    def _constant(self, rep: str) -> Doc:
        return Text(canonicalize_identifier(rep))

    def _var(self, rep: str) -> Doc:
        return Text(canonicalize_identifier(rep))

    def _finish_apply(self, node: terms.Apply, relsym_ret: Doc, args_ret: list[Doc]):
        return relsym_ret + utils.enclosed("(", utils.join(args_ret, ", "), ")")

    def _finish_binop(self, node: terms.BinOp, lhs_ret: Doc, rhs_ret: Doc):
        return lhs_ret + utils.padded(node.op) + rhs_ret

    def _finish_exists(self, node: terms.Exists, vs: list[Binding[Doc]], expr: Doc):
        return Text("Exists (TODO);")

    def _finish_forall(self, node: terms.Forall, vs: list[Binding[Doc]], expr: Doc):
        return Text("Forall (TODO);")

    def _finish_ite(self, node: terms.Ite, test: Doc, then: Doc, els: Doc):
        return test + utils.padded("?") + then + utils.padded(":") + els

    def _finish_some(self, none: terms.Some, vs: list[Binding[Doc]], fmla: Doc):
        raise NotImplementedError()

    def _finish_unop(self, node: terms.UnOp, expr: Doc):
        if isinstance(expr, Text):
            return Text(node.op) + expr
        return Text(node.op) + utils.enclosed("(", expr, ")")

    # Actions

    def _finish_assert(self, act: terms.Assert, pred: Doc):
        return Text("this.assert(") + pred + Text(");")

    def _finish_assign(self, act: terms.Assign, lhs: Doc, rhs: Doc):
        return lhs + utils.padded("=") + rhs + semi

    def _finish_assume(self, act: terms.Assume, pred: Doc):
        return Text("this.assume(") + pred + Text(");")

    def _finish_call(self, act: terms.Call, app: Doc):
        return app + semi  # XXX: yes??

    def _finish_debug(self, act: terms.Debug, args: list[Doc]):
        return Text("this.debug(") + Text(act.msg) + Text(");")  # TODO: args

    def _finish_ensures(self, act: terms.Ensures, pred: Doc):
        return Text("this.ensures(") + pred + Text(")")

    def _finish_havok(self, act: terms.Havok, modifies: list[Doc]):
        return Nil()  # TODO: ???

    def _finish_if(self, act: terms.If, test: Doc, then: Doc, els: Optional[Doc]) -> Doc:
        if_block = Text("if (") + test + Text(")")
        ret = if_block + utils.space + block(then)
        if els is not None:
            ret = ret + utils.padded(Text("else")) + block(els)
        return ret

    def _finish_let(self, act: terms.Let, scope: Doc):
        var_docs = []
        for binding in act.vardecls:
            var = Text(binding.name)
            sort_name = binding.decl

            sort = UnboxedSort().visit_sort(self.sorts[sort_name])

            var_docs.append(sort + utils.space + var + semi)
        return utils.join(var_docs, Line()) + Line() + scope

    def _finish_sequence(self, act: terms.Sequence, stmts: list[Doc]) -> Doc:
        return utils.join(stmts, Line())
