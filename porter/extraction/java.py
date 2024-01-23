from porter.ast import Binding, sorts, terms
from porter.ast.visitor import Visitor
from porter.pp import Doc, Text, Line, Nest, Concat, Choice, utils

from typing import Optional

semi = Text(";")


def block(contents: Doc) -> Doc:
    return Text("{") + Nest(2, contents) + Text("}")


class Extractor(Visitor[Doc]):
    # Sorts

    def bool(self):
        # TODO: Java sorts will need to know whether they're to be boxed or not!
        return Text("bool")

    def bv(self):
        raise NotImplementedError()

    def enum(self, discriminants: list[str]):
        raise NotImplementedError()

    def _finish_function(self, node: sorts.Function, domain: list[Doc], range: Doc):
        raise NotImplementedError()

    def numeric(self, lo: Optional[int], hi: Optional[int]):
        return Text("int")

    def uninterpreted(self):
        return Text("int")

    # Expressions

    def _constant(self, rep: str) -> Doc:
        return Text(rep)

    def _finish_apply(self, node: terms.Apply, relsym_ret: Doc, args_ret: list[Doc]):
        return relsym_ret + utils.enclosed("(", utils.sep(args_ret, utils.soft_comma), ")")

    def _finish_binop(self, node: terms.BinOp, lhs_ret: Doc, rhs_ret: Doc):
        return lhs_ret + utils.padded(node.op) + rhs_ret

    def _finish_exists(self, node: terms.Exists, vs: list[Binding[Doc]], expr: Doc):
        raise NotImplementedError()

    def _finish_forall(self, node: terms.Forall, vs: list[Binding[Doc]], expr: Doc):
        raise NotImplementedError()

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
        raise NotImplementedError()

    def _finish_assign(self, act: terms.Assign, lhs: Doc, rhs: Doc):
        return lhs + utils.padded("=") + rhs + semi

    def _finish_assume(self, act: terms.Assume, pred: Doc):
        raise NotImplementedError()

    def _finish_call(self, act: terms.Call, app: Doc):
        return app + semi  # XXX: yes??

    def _finish_debug(self, act: terms.Debug, args: list[Doc]):
        raise NotImplementedError()

    def _finish_ensures(self, act: terms.Ensures, pred: Doc):
        raise NotImplementedError()

    def _finish_havok(self, act: terms.Havok, modifies: list[Doc]):
        raise NotImplementedError()

    def _finish_if(self, act: terms.If, test: Doc, then: Doc, els: Optional[Doc]) -> Doc:
        if_block = Text("if (") + test + Text(")")
        ret = if_block + utils.space + block(then)
        if els is not None:
            ret = ret + utils.padded(Text("else")) + block(els)
        return ret

    def _finish_let(self, act: terms.Let, vardecls: list[Binding[Doc]], scope: Doc):
        var_docs = []
        for binding in vardecls:
            var = Text(binding.name)
            sort = binding.decl
            var_docs.append(sort + utils.space + var + semi)
        return utils.sep(var_docs, Line()) + Line() + scope

    def _finish_sequence(self, act: terms.Sequence, stmts: list[Doc]) -> Doc:
        return utils.sep(stmts, Line())